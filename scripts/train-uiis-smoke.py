"""Short pipeline test on the original UIIS split; not a final baseline recipe."""
import argparse
import json
from pathlib import Path

import mmdet
import torch
from mmengine.config import Config
from mmengine.runner import Runner
from mmdet.utils import register_all_modules

ROOT = Path(__file__).resolve().parents[1]
CLASSES = ('fish', 'reefs', 'aquatic plants', 'wrecks/ruins',
           'human divers', 'robots', 'sea-floor')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-iters', type=int, required=True)
    parser.add_argument('--work-dir', required=True)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    register_all_modules()
    base = Path(mmdet.__file__).parent / '.mim/configs/mask2former/mask2former_r50_8xb2-lsj-50e_coco.py'
    cfg = Config.fromfile(str(base))
    cfg.model.backbone.init_cfg = None  # Reuse full COCO checkpoint, no extra download.
    cfg.model.panoptic_head.num_things_classes = 7
    cfg.model.panoptic_head.num_stuff_classes = 0
    cfg.model.panoptic_head.loss_cls.class_weight = [1.0] * 7 + [0.1]
    cfg.model.panoptic_fusion_head.num_things_classes = 7
    cfg.model.panoptic_fusion_head.num_stuff_classes = 0
    cfg.model.data_preprocessor.batch_augments[0].size = (512, 512)
    train_pipeline = [
        dict(type='LoadImageFromFile', to_float32=True),
        dict(type='LoadAnnotations', with_bbox=True, with_mask=True),
        dict(type='RandomFlip', prob=0.5),
        dict(type='Resize', scale=(512, 512), keep_ratio=True),
        dict(type='FilterAnnotations', min_gt_bbox_wh=(1e-5, 1e-5), by_mask=True),
        dict(type='PackDetInputs'),
    ]
    test_pipeline = [
        dict(type='LoadImageFromFile', to_float32=True),
        dict(type='Resize', scale=(512, 512), keep_ratio=True),
        dict(type='LoadAnnotations', with_bbox=True, with_mask=True),
        dict(type='PackDetInputs', meta_keys=('img_id', 'img_path', 'ori_shape', 'img_shape', 'scale_factor')),
    ]
    data_root = str(ROOT / 'data/UIIS') + '/'
    def dataset(split, pipeline, test_mode):
        return dict(type='CocoDataset', data_root=data_root,
                    ann_file=f'annotations/{split}.json', data_prefix=dict(img=split + '/'),
                    metainfo=dict(classes=CLASSES), pipeline=pipeline,
                    test_mode=test_mode, filter_cfg=None)
    cfg.train_dataloader = dict(batch_size=1, num_workers=2, persistent_workers=True,
                                sampler=dict(type='InfiniteSampler', shuffle=True),
                                dataset=dataset('train', train_pipeline, False))
    cfg.val_dataloader = dict(batch_size=1, num_workers=2, persistent_workers=True,
                              sampler=dict(type='DefaultSampler', shuffle=False),
                              drop_last=False, dataset=dataset('val', test_pipeline, True))
    cfg.test_dataloader = cfg.val_dataloader
    cfg.val_evaluator = dict(type='CocoMetric', ann_file=data_root + 'annotations/val.json',
                             metric=['bbox', 'segm'], classwise=True)
    cfg.test_evaluator = cfg.val_evaluator
    cfg.train_cfg = dict(type='IterBasedTrainLoop', max_iters=args.max_iters,
                         val_begin=100, val_interval=100)
    cfg.param_scheduler = []
    cfg.default_hooks.checkpoint.update(interval=50, max_keep_ckpts=2, save_last=True)
    cfg.default_hooks.logger.interval = 10
    cfg.log_processor = dict(type='LogProcessor', window_size=10, by_epoch=False)
    cfg.randomness = dict(seed=20261012)
    cfg.work_dir = str(Path(args.work_dir).resolve())
    cfg.load_from = str(ROOT / 'checkpoints/mask2former_r50_8xb2-lsj-50e_coco_20220506_191028-41b088b6.pth')
    cfg.resume = args.resume
    if args.resume:
        cfg.load_from = str(Path(cfg.work_dir) / 'iter_50.pth')
    cfg.visualizer.vis_backends = [dict(type='LocalVisBackend')]
    cfg.dump(str(ROOT / 'reports' / f'uiis-smoke-config-{args.max_iters}.py'))
    torch.cuda.reset_peak_memory_stats()
    runner = Runner.from_cfg(cfg)
    runner.train()
    assert runner.iter == args.max_iters
    metrics = {k: float(v.current()) for k, v in runner.message_hub.log_scalars.items()
               if k.startswith('val/')}
    losses = {k: float(v.current()) for k, v in runner.message_hub.log_scalars.items()
              if k.startswith('train/') and 'loss' in k}
    assert losses and all(torch.isfinite(torch.tensor(v)) for v in losses.values())
    if args.max_iters >= 100:
        assert any('segm_mAP' in k for k in metrics), 'Segmentation evaluation missing'
    summary = dict(iterations=runner.iter, resumed=args.resume,
                   work_dir=cfg.work_dir, last_losses=losses, metrics=metrics,
                   peak_gpu_mib=torch.cuda.max_memory_allocated() / 1024**2,
                   note='Pipeline smoke test only: 512px, batch 1, official split including known duplicate; not final accuracy.')
    (ROOT / 'reports' / f'uiis-smoke-{args.max_iters}.json').write_text(json.dumps(summary, indent=2))
    print('UIIS_SMOKE_STAGE_OK', args.max_iters, flush=True)


if __name__ == '__main__':
    main()
