"""Epoch training entry: first epoch gate, then explicit resume. Linux server only."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import math
import shutil
from pathlib import Path

import torch
from mmengine.hooks import Hook
from mmengine.runner import Runner
from mmdet.utils import register_all_modules

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('baseline_config', ROOT / 'scripts/prepare-uiis-baseline.py')
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)


class TrainingGuard(Hook):
    priority = 'LOWEST'  # After scheduler and checkpoint hooks.

    def __init__(self, stop_epoch, archive_epochs, resume_checkpoint=None):
        self.stop_epoch = stop_epoch
        self.archive_epochs = archive_epochs
        self.resume_checkpoint = resume_checkpoint
        self.resume_verified = False

    def before_train(self, runner):
        if self.resume_checkpoint:
            saved = torch.load(self.resume_checkpoint, map_location='cpu')
            current = runner.optim_wrapper.optimizer.state_dict()
            assert runner.epoch == saved['meta']['epoch']
            assert runner.iter == saved['meta']['iter']
            assert current['param_groups'] == saved['optimizer']['param_groups']
            assert len(current['state']) == len(saved['optimizer']['state']) > 0
            for key, state in saved['optimizer']['state'].items():
                for field, value in state.items():
                    actual = current['state'][key][field]
                    if torch.is_tensor(value):
                        assert torch.equal(actual.cpu(), value), (key, field)
                    else:
                        assert actual == value, (key, field)
            assert [s.state_dict() for s in runner.param_schedulers] == saved['param_schedulers']
            self.resume_verified = True
            runner.logger.info('RESUME_STATE_VERIFIED: epoch, iteration, optimizer and scheduler')

    def after_train_iter(self, runner, batch_idx, data_batch=None, outputs=None):
        values = [float(v.current()) for k, v in runner.message_hub.log_scalars.items()
                  if k.startswith('train/') and 'loss' in k]
        if not values or not all(math.isfinite(v) for v in values):
            raise RuntimeError('Nonfinite/missing training losses; stopping without overwriting prior checkpoints')

    def after_train_epoch(self, runner):
        epoch = runner.epoch + 1
        checkpoint = Path(runner.work_dir) / f'epoch_{epoch}.pth'
        if not checkpoint.is_file():
            raise RuntimeError(f'Expected checkpoint not saved: {checkpoint}')
        if epoch in self.archive_epochs:
            archive = Path(runner.work_dir) / 'milestones'
            archive.mkdir(exist_ok=True)
            target = archive / checkpoint.name
            temporary = target.with_suffix('.pth.tmp')
            shutil.copyfile(checkpoint, temporary)
            temporary.replace(target)
        if self.stop_epoch and epoch >= self.stop_epoch:
            runner.train_loop.stop_training = True
            runner.logger.info('FIRST_EPOCH_GATE: checkpoint saved; stopping for inspection')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', choices=['first', 'resume'], required=True)
    parser.add_argument('--work-dir', required=True)
    parser.add_argument('--verification', action='store_true', help='4-image/5-mini-epoch integration check only')
    args = parser.parse_args()
    work = Path(args.work_dir).resolve()
    if ROOT / 'work_dirs' not in work.parents:
        raise ValueError('work-dir must be a child of project work_dirs')
    (ROOT / 'work_dirs').mkdir(exist_ok=True)
    # All invocations share this lock; it is automatically released after crashes.
    with (ROOT / 'work_dirs/uiis-training.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit('TRAINING_ALREADY_RUNNING: project training lock is held')
        register_all_modules()
        cfg = baseline.build_config()
        cfg.work_dir = str(work)
        archive_epochs = [12, 24, 36]
        if args.verification:
            cfg.train_dataloader.dataset.indices = 4
            cfg.train_cfg.max_epochs = 5
            cfg.param_scheduler[0].update(end=5, milestones=[2, 4])
            cfg.default_hooks.logger.interval = 1
            archive_epochs = [1, 3, 5]
        protocol = dict(verification=args.verification, epochs=cfg.train_cfg.max_epochs,
                        train_sha256=hashlib.sha256((ROOT / 'data/UIIS/annotations/train.json').read_bytes()).hexdigest(),
                        config=cfg.pretty_text)
        marker = work / 'run-protocol.json'
        checkpoint = None
        if args.stage == 'first':
            if work.exists() and any(work.iterdir()):
                raise ValueError('Refusing to overwrite an existing run; use resume or a new work-dir')
            work.mkdir(parents=True, exist_ok=True)
            marker.write_text(json.dumps(protocol, indent=2))
        else:
            if json.loads(marker.read_text()) != protocol:
                raise ValueError('Run protocol differs; refuse an incompatible resume')
            checkpoint = Path((work / 'last_checkpoint').read_text().strip()).resolve()
            if checkpoint.parent != work or not checkpoint.is_file():
                raise ValueError('Invalid latest checkpoint path')
            meta = torch.load(checkpoint, map_location='cpu')['meta']
            if meta['epoch'] >= cfg.train_cfg.max_epochs:
                raise ValueError('Run already reached its configured training budget')
            cfg.resume = True
            cfg.load_from = str(checkpoint)
        cfg.dump(str(work / f'config-{args.stage}.py'))
        runner = Runner.from_cfg(cfg)
        guard = TrainingGuard(1 if args.stage == 'first' else None, archive_epochs, checkpoint)
        runner.register_hook(guard)
        runner.train()
        expected = 1 if args.stage == 'first' else cfg.train_cfg.max_epochs
        assert runner.epoch == expected
        report = dict(stage=args.stage, verification=args.verification, completed_epochs=runner.epoch,
                      completed_iterations=runner.iter, resume_state_verified=guard.resume_verified,
                      optimizer_lrs=[g['lr'] for g in runner.optim_wrapper.optimizer.param_groups],
                      checkpoint=str(work / f'epoch_{runner.epoch}.pth'))
        (work / f'result-{args.stage}.json').write_text(json.dumps(report, indent=2))
        print('UIIS_TRAIN_STAGE_OK', args.stage, runner.epoch, flush=True)


if __name__ == '__main__':
    main()
