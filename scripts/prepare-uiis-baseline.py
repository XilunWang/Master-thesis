"""Prepare a baseline candidate and optionally profile 20 training steps only."""
import argparse
import json
import math
import time
from pathlib import Path

import mmdet
import torch
from mmengine.config import Config
from mmengine.hooks import Hook
from mmengine.runner import Runner
from mmdet.utils import register_all_modules

ROOT = Path(__file__).resolve().parents[1]
CLASSES = ('fish', 'reefs', 'aquatic plants', 'wrecks/ruins',
           'human divers', 'robots', 'sea-floor')


def build_config():
    base = Path(mmdet.__file__).parent / '.mim/configs/mask2former/mask2former_r50_8xb2-lsj-50e_coco.py'
    cfg = Config.fromfile(str(base))
    cfg.model.backbone.init_cfg = None
    cfg.model.panoptic_head.num_things_classes = 7
    cfg.model.panoptic_head.num_stuff_classes = 0
    cfg.model.panoptic_head.loss_cls.class_weight = [1.] * 7 + [.1]
    cfg.model.panoptic_fusion_head.num_things_classes = 7
    cfg.model.panoptic_fusion_head.num_stuff_classes = 0
    for split, key in [('train', 'train_dataloader'), ('val', 'val_dataloader')]:
        cfg[key] = dict(
            batch_size=2 if split == 'train' else 1,
            num_workers=2, persistent_workers=True, drop_last=False,
            sampler=dict(type='DefaultSampler', shuffle=split == 'train'),
            dataset=dict(type='CocoDataset', data_root=str(ROOT / 'data/UIIS') + '/',
                         ann_file=f'annotations/{split}.json', data_prefix=dict(img=split + '/'),
                         metainfo=dict(classes=CLASSES), filter_cfg=None,
                         test_mode=split != 'train',
                         pipeline=cfg.train_pipeline if split == 'train' else cfg.test_pipeline))
    cfg.test_dataloader = cfg.val_dataloader
    cfg.test_evaluator = dict(type='CocoMetric',
        ann_file=str(ROOT / 'data/UIIS/annotations/val.json'), metric=['bbox', 'segm'], classwise=True)
    # No periodic test-set evaluation or best-checkpoint selection until agreed.
    cfg.val_dataloader = None
    cfg.val_evaluator = None
    cfg.val_cfg = None
    cfg.train_cfg = dict(type='EpochBasedTrainLoop', max_epochs=36, val_interval=37)
    cfg.param_scheduler = [dict(type='MultiStepLR', begin=0, end=36, by_epoch=True,
                               milestones=[27, 33], gamma=.1)]
    cfg.optim_wrapper.type = 'OptimWrapper'  # FP32 first; no untested AMP assumption.
    cfg.optim_wrapper.optimizer.lr = .0001
    cfg.auto_scale_lr = dict(enable=False, base_batch_size=16)
    cfg.default_hooks.checkpoint = dict(type='CheckpointHook', by_epoch=True,
        interval=1, max_keep_ckpts=3, save_last=True)
    cfg.default_hooks.logger.interval = 50
    cfg.log_processor = dict(type='LogProcessor', window_size=50, by_epoch=True)
    cfg.randomness = dict(seed=20261012)
    cfg.load_from = str(ROOT / 'checkpoints/mask2former_r50_8xb2-lsj-50e_coco_20220506_191028-41b088b6.pth')
    cfg.resume = False
    cfg.work_dir = str(ROOT / 'work_dirs/uiis_baseline_candidate')
    cfg.visualizer.vis_backends = [dict(type='LocalVisBackend')]
    return cfg


class ProfileHook(Hook):
    priority = 'VERY_HIGH'

    def __init__(self):
        self.rows = []

    def before_train_iter(self, runner, batch_idx, data_batch=None):
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        self.start = time.perf_counter()

    def after_train_iter(self, runner, batch_idx, data_batch=None, outputs=None):
        torch.cuda.synchronize()
        losses = {k: float(v.current()) for k, v in runner.message_hub.log_scalars.items()
                  if k.startswith('train/') and 'loss' in k}
        assert losses and all(math.isfinite(v) for v in losses.values()), losses
        self.rows.append(dict(step=runner.iter + 1, compute_seconds=time.perf_counter() - self.start,
                              allocated_mib=torch.cuda.max_memory_allocated() / 1024**2,
                              reserved_mib=torch.cuda.max_memory_reserved() / 1024**2,
                              loss=losses['train/loss']))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', action='store_true', help='Run exactly 20 steps, no evaluation.')
    args = parser.parse_args()
    register_all_modules()
    reports = ROOT / 'reports'
    reports.mkdir(exist_ok=True)
    cfg = build_config()
    cfg.dump(str(reports / 'uiis-baseline-candidate.py'))
    train = json.loads((ROOT / 'data/UIIS/annotations/train.json').read_text())
    test = json.loads((ROOT / 'data/UIIS/annotations/val.json').read_text())
    assert len(train['images']) == 3937 and len(test['images']) == 691
    assert tuple(c['name'] for c in sorted(train['categories'], key=lambda c: c['id'])) == CLASSES
    assert any(i['file_name'] == 'XL_266.jpg' for i in train['images'])
    assert any(i['file_name'] == 'XL_679.jpg' for i in test['images'])
    print('BASELINE_CONFIG_OK', flush=True)
    if not args.profile:
        return
    cfg.work_dir = str(ROOT / 'work_dirs' / ('uiis_profile_' + time.strftime('%Y%m%d_%H%M%S')))
    cfg.train_cfg = dict(type='IterBasedTrainLoop', max_iters=20, val_interval=21)
    cfg.train_dataloader.sampler = dict(type='InfiniteSampler', shuffle=True)
    cfg.param_scheduler = []  # First 20 steps have the same constant LR as candidate.
    cfg.default_hooks.checkpoint = None
    cfg.default_hooks.logger.interval = 5
    cfg.log_processor = dict(type='LogProcessor', window_size=5, by_epoch=False)
    cfg.dump(str(reports / 'uiis-baseline-profile-config.py'))
    runner = Runner.from_cfg(cfg)
    hook = ProfileHook()
    runner.register_hook(hook)
    start = time.perf_counter()
    runner.train()
    assert runner.iter == 20 and len(hook.rows) == 20
    result = dict(steps=20, batch_size=2, images=40, precision='FP32',
        train_wall_seconds=time.perf_counter() - start,
        mean_compute_seconds_after_warmup=sum(r['compute_seconds'] for r in hook.rows[5:]) / 15,
        peak_allocated_mib=max(r['allocated_mib'] for r in hook.rows),
        peak_reserved_mib=max(r['reserved_mib'] for r in hook.rows), rows=hook.rows,
        note='20-step capacity probe only; compute timing excludes data loading. No accuracy evaluation or formal training.')
    (reports / 'uiis-baseline-profile.json').write_text(json.dumps(result, indent=2))
    print('BASELINE_PROFILE_OK', flush=True)


if __name__ == '__main__':
    main()
