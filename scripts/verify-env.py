"""Check binary compatibility and CUDA forward/backward used by Mask2Former."""
import json
import platform

import mmcv
import mmdet
import mmengine
import numpy
import torch
import torchvision
from mmcv.ops import MultiScaleDeformableAttention, nms
from mmdet.utils import register_all_modules

assert torch.cuda.is_available(), 'CUDA unavailable'
register_all_modules()
print(json.dumps({
    'python': platform.python_version(), 'torch': torch.__version__,
    'torchvision': torchvision.__version__, 'cuda': torch.version.cuda,
    'gpu': torch.cuda.get_device_name(0), 'numpy': numpy.__version__,
    'mmcv': mmcv.__version__, 'mmengine': mmengine.__version__,
    'mmdet': mmdet.__version__,
}, indent=2), flush=True)
layer = MultiScaleDeformableAttention(
    embed_dims=32, num_heads=4, num_levels=1, num_points=4,
    batch_first=True).cuda()
query = torch.randn(1, 4, 32, device='cuda', requires_grad=True)
output = layer(query, reference_points=torch.rand(1, 4, 1, 2, device='cuda'),
               spatial_shapes=torch.tensor([[2, 2]], device='cuda'),
               level_start_index=torch.tensor([0], device='cuda'))
output.square().mean().backward()
assert torch.isfinite(output).all() and torch.isfinite(query.grad).all()
boxes = torch.tensor([[0., 0., 10., 10.], [1., 1., 9., 9.]], device='cuda')
_, keep = nms(boxes, torch.tensor([0.9, 0.8], device='cuda'), 0.5)
assert keep.numel() == 1
torch.cuda.synchronize()
print('PASS: MMDetection imports, CUDA deformable attention forward/backward, CUDA NMS')
