"""Download the official COCO instance model and run a single-image GPU demo."""
import hashlib
import json
from pathlib import Path
import time
import urllib.request

import mmcv
import mmdet
import torch
from mmdet.apis import inference_detector, init_detector
from mmdet.registry import VISUALIZERS
from mmdet.utils import register_all_modules

ROOT = Path(__file__).resolve().parents[1]
NAME = 'mask2former_r50_8xb2-lsj-50e_coco'
WEIGHT_NAME = NAME + '_20220506_191028-41b088b6.pth'
WEIGHT_URL = 'https://download.openmmlab.com/mmdetection/v3.0/mask2former/' + NAME + '/' + WEIGHT_NAME
IMAGE_URL = 'https://raw.githubusercontent.com/open-mmlab/mmdetection/v3.3.0/demo/demo.jpg'


def main():
    assert torch.cuda.is_available(), 'CUDA unavailable'
    register_all_modules()
    config = Path(mmdet.__file__).parent / '.mim/configs/mask2former' / (NAME + '.py')
    if not config.is_file():
        raise FileNotFoundError(f'Installed MMDetection config missing: {config}')
    weights = ROOT / 'checkpoints' / WEIGHT_NAME
    output = ROOT / 'reports/demo-mask2former'
    weights.parent.mkdir(exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    if not weights.exists():
        print('Downloading official checkpoint...', flush=True)
        torch.hub.download_url_to_file(WEIGHT_URL, str(weights), hash_prefix='41b088b6')
    digest = hashlib.sha256()
    with weights.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    assert digest.hexdigest().startswith('41b088b6'), 'Checkpoint checksum mismatch'
    image_path = output / 'input.jpg'
    if not image_path.exists():
        with urllib.request.urlopen(IMAGE_URL, timeout=60) as response:
            image_path.write_bytes(response.read())
    model = init_detector(str(config), str(weights), device='cuda:0')
    torch.cuda.reset_peak_memory_stats()
    torch.cuda.synchronize()
    start = time.perf_counter()
    result = inference_detector(model, str(image_path))
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - start
    prediction = result.pred_instances
    assert torch.isfinite(prediction.scores).all(), 'Non-finite prediction scores'
    assert hasattr(prediction, 'masks'), 'Instance masks missing'
    count = int((prediction.scores >= 0.5).sum().item())
    assert count > 0, 'No detections above 0.5 on the official demo image'
    visualizer = VISUALIZERS.build(model.cfg.visualizer)
    visualizer.dataset_meta = model.dataset_meta
    visualizer.add_datasample('demo', mmcv.imread(str(image_path), channel_order='rgb'),
                             data_sample=result, draw_gt=False, pred_score_thr=0.5,
                             out_file=str(output / 'prediction.jpg'))
    summary = {
        'model': NAME, 'dataset': 'COCO (not UIIS)',
        'weight_url': WEIGHT_URL, 'image_url': IMAGE_URL,
        'checkpoint_sha256': digest.hexdigest(),
        'instances_score_ge_0.5': count,
        'first_inference_seconds': elapsed,
        'peak_allocated_gpu_mib': torch.cuda.max_memory_allocated() / 1024**2,
        'note': 'First-call demo timing is not a throughput benchmark or accuracy evaluation.',
    }
    (output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))
    print('MASK2FORMER_DEMO_OK', flush=True)


if __name__ == '__main__':
    main()
