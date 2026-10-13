"""Render the evaluation report and fixed, unselected test examples."""
import json
from pathlib import Path

import cv2
import numpy as np
from pycocotools.coco import COCO
from pycocotools import mask as mask_utils

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/uiis-baseline-36e-evaluation'


def main():
    result = json.loads((OUT / 'metrics.json').read_text())
    metrics = result['metrics']
    lines = ['# Mask2Former R50：UIIS 36 轮基线评估', '',
             '固定使用第 36 轮权重，完整评估官方 691 张测试图。未按测试成绩选择权重；原始划分及已知跨划分重复图片保持不变。', '',
             '## 整体指标（0–100 分）', '',
             '| 任务 | AP | AP50 | AP75 | 小目标 AP | 中目标 AP | 大目标 AP |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for kind, name in [('segm', '实例掩码分割'), ('bbox', '检测框')]:
        values = [metrics[f'coco/{kind}_mAP{suffix}'] * 100
                  for suffix in ['', '_50', '_75', '_s', '_m', '_l']]
        lines.append('| ' + name + ' | ' + ' | '.join(f'{v:.1f}' for v in values) + ' |')
    lines.extend(['', 'AP 是按标准 COCO 规则计算的平均精度，不是“有多少像素分对”的百分比。当前关注 segm 指标。', '',
                  '## 分类别指标（0–100 分）', '', '| 指标 | 数值 |', '| --- | ---: |'])
    for key, value in metrics.items():
        if key.endswith('_precision'):
            lines.append(f'| {key} | {value * 100:.1f} |')
    lines.extend(['', '## 可视化', '',
                  '固定展示标注列表前 6 张图片，未筛选效果。每张左侧为人工标注，右侧为预测；仅画出置信度 ≥ 0.5 的预测。此显示阈值不用于修改 AP 计算。', ''])
    coco = COCO(str(ROOT / 'data/UIIS/annotations/val.json'))
    predictions = json.loads((OUT / 'predictions.segm.json').read_text())
    grouped = {}
    for item in predictions:
        grouped.setdefault(item['image_id'], []).append(item)
    palette = [(50, 120, 240), (80, 210, 80), (220, 130, 40), (180, 80, 200),
               (60, 200, 220), (200, 200, 60), (180, 100, 100)]
    images = OUT / 'examples'
    images.mkdir(exist_ok=True)
    for image_id in list(coco.imgs)[:6]:
        item = coco.imgs[image_id]
        raw = cv2.imread(str(ROOT / 'data/UIIS/val' / item['file_name']))
        assert raw is not None
        panels = []
        for name, annotations in [('Ground truth', coco.imgToAnns[image_id]),
                                  ('Prediction score >= 0.5', grouped.get(image_id, []))]:
            canvas = raw.copy()
            for ann in annotations:
                if 'score' in ann and ann['score'] < .5:
                    continue
                mask = (mask_utils.decode(ann['segmentation']) if 'score' in ann
                        else coco.annToMask(ann)).astype(bool)
                color = palette[(ann['category_id'] - 1) % len(palette)]
                canvas[mask] = (canvas[mask] * .55 + np.array(color) * .45).astype(np.uint8)
                contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cv2.drawContours(canvas, contours, -1, color, 1)
            scale = min(1., 640 / canvas.shape[1])
            canvas = cv2.resize(canvas, None, fx=scale, fy=scale)
            canvas = cv2.copyMakeBorder(canvas, 32, 0, 0, 0, cv2.BORDER_CONSTANT)
            cv2.putText(canvas, name, (8, 23), cv2.FONT_HERSHEY_SIMPLEX, .6, (255, 255, 255), 1)
            panels.append(canvas)
        filename = f'{image_id}.jpg'
        assert cv2.imwrite(str(images / filename), np.concatenate(panels, axis=1))
        lines.append(f"### {item['file_name']}\n\n![人工标注与预测](examples/{filename})\n")
    lines.extend(['## 可追溯记录', '', f"- 完成评估图片数：{result['evaluated_images']}",
                  f"- 权重 SHA256：`{result['checkpoint_sha256']}`",
                  f"- 测试标注 SHA256：`{result['annotations_sha256']}`",
                  '- 完整指标：metrics.json；配置：evaluation-config.py；预测：predictions.bbox.json / predictions.segm.json；日志：console.log。',
                  '- 与 WaterMask 的论文数字比较前，仍需核对训练预算、预训练与评估设置。该结果不证明加入边界模块一定有效。', ''])
    (OUT / 'report.md').write_text('\n'.join(lines), encoding='utf-8')
    print('EVALUATION_REPORT_OK')


if __name__ == '__main__':
    main()
