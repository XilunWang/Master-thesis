"""Evaluate the fixed final baseline checkpoint on the complete official UIIS test split."""
import fcntl
import hashlib
import json
import math
import time
from pathlib import Path

import torch
from mmengine.config import Config
from mmengine.hooks import Hook
from mmengine.runner import Runner
from mmdet.utils import register_all_modules

ROOT = Path(__file__).resolve().parents[1]


class CountImages(Hook):
    def __init__(self):
        self.ids = []

    def after_test_iter(self, runner, batch_idx, data_batch=None, outputs=None):
        self.ids.extend(int(sample.img_id) for sample in outputs)


def main():
    work = ROOT / 'work_dirs/uiis_baseline_r50_36e'
    output = ROOT / 'reports/uiis-baseline-36e-evaluation'
    output.mkdir(parents=True, exist_ok=True)
    with (ROOT / 'work_dirs/uiis-training.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (output / 'metrics.json').exists():
            raise RuntimeError('Completed evaluation exists; refusing to overwrite')
        checkpoint = work / 'epoch_36.pth'
        saved = torch.load(checkpoint, map_location='cpu')
        assert saved['meta']['epoch'] == 36 and saved['meta']['iter'] == 70884
        del saved
        annotations = ROOT / 'data/UIIS/annotations/val.json'
        test = json.loads(annotations.read_text())
        expected_ids = {int(item['id']) for item in test['images']}
        assert len(test['images']) == len(expected_ids) == 691
        cfg = Config.fromfile(str(work / 'config-resume.py'))
        cfg.load_from = str(checkpoint)
        cfg.resume = False
        cfg.work_dir = str(output / 'runner')
        cfg.test_evaluator.classwise = True
        cfg.test_evaluator.outfile_prefix = str(output / 'predictions')
        cfg.dump(str(output / 'evaluation-config.py'))
        register_all_modules()
        runner = Runner.from_cfg(cfg)
        counter = CountImages()
        runner.register_hook(counter)
        start = time.time()
        metrics = runner.test()
        assert len(counter.ids) == 691 and set(counter.ids) == expected_ids
        metrics = {key: float(value) for key, value in metrics.items()}
        assert metrics and all(math.isfinite(value) for value in metrics.values())
        result = dict(completed=True, evaluated_images=len(counter.ids), epoch=36,
                      iterations=70884, checkpoint=str(checkpoint),
                      checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
                      annotations_sha256=hashlib.sha256(annotations.read_bytes()).hexdigest(),
                      seconds=time.time() - start, metrics=metrics,
                      protocol='Final epoch, official 691-image test split, original duplicate retained; no test-set checkpoint selection.')
        (output / 'metrics.json').write_text(json.dumps(result, indent=2))
        print('UIIS_EVALUATION_OK', json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
