"""Audit original COCO annotations without modifying the official split."""
from collections import Counter
import hashlib
import json
from pathlib import Path

from PIL import Image
import numpy as np
from pycocotools.coco import COCO

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/UIIS'


def main():
    report = {'source': 'https://huggingface.co/datasets/LiamLian0727/UIIS',
              'splits': {}, 'errors': [], 'warnings': []}
    hashes = {}
    category_lists = []
    for split, expected in [('train', 3937), ('val', 691)]:
        path = DATA / 'annotations' / (split + '.json')
        raw = json.loads(path.read_text())
        coco = COCO(str(path))
        category_lists.append(raw['categories'])
        assert len(raw['images']) == expected, (split, len(raw['images']))
        assert len(coco.imgs) == len(raw['images']), 'Duplicate image IDs'
        assert len(coco.anns) == len(raw['annotations']), 'Duplicate annotation IDs'
        hashes[split] = {}
        for image in raw['images']:
            file = DATA / split / image['file_name']
            assert DATA.resolve() in file.resolve().parents, 'Unsafe image path'
            with Image.open(file) as decoded:
                decoded.load()
                if decoded.size != (image['width'], image['height']):
                    report['errors'].append([split, image['id'], 'image size mismatch'])
            hashes[split][hashlib.sha256(file.read_bytes()).hexdigest()] = image['file_name']
        empty_masks = []
        counts = Counter()
        for ann in raw['annotations']:
            assert ann['image_id'] in coco.imgs, 'Unknown image ID'
            assert ann['category_id'] in coco.cats, 'Unknown category ID'
            counts[ann['category_id']] += 1
            try:
                mask = coco.annToMask(ann)
                if not mask.any():
                    empty_masks.append(ann['id'])
                if len(ann['bbox']) != 4 or not np.isfinite(ann['bbox']).all():
                    raise ValueError('Invalid bbox')
            except Exception as error:
                report['errors'].append([split, ann['id'], str(error)])
        report['splits'][split] = {
            'images': len(raw['images']), 'instances': len(raw['annotations']),
            'categories': raw['categories'], 'category_instance_counts': dict(counts),
            'empty_masks': empty_masks,
            'annotation_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        if empty_masks:
            report['warnings'].append(f'{split}: {len(empty_masks)} empty masks')
        # Save one original/ground-truth pair to inspect annotation alignment.
        sample = raw['images'][0]
        with Image.open(DATA / split / sample['file_name']) as source:
            original = source.convert('RGB')
        overlay = np.array(original, dtype=np.float32)
        colors = np.array([[255, 70, 70], [70, 220, 70], [70, 120, 255],
                           [255, 200, 40], [220, 70, 220], [40, 220, 220], [180, 140, 80]])
        for ann in coco.imgToAnns[sample['id']]:
            mask = coco.annToMask(ann).astype(bool)
            overlay[mask] = 0.5 * overlay[mask] + 0.5 * colors[(ann['category_id'] - 1) % len(colors)]
        preview = Image.new('RGB', (original.width * 2, original.height))
        preview.paste(original, (0, 0))
        preview.paste(Image.fromarray(overlay.astype(np.uint8)), (original.width, 0))
        (ROOT / 'reports').mkdir(exist_ok=True)
        preview.save(ROOT / 'reports' / f'uiis-ground-truth-{split}.jpg')
        report['splits'][split]['preview_image'] = sample['file_name']
        print(split, len(raw['images']), 'images checked;', len(raw['annotations']), 'masks decoded', flush=True)
    assert category_lists[0] == category_lists[1], 'Category lists differ'
    duplicates = set(hashes['train']) & set(hashes['val'])
    report['cross_split_exact_duplicates'] = [
        [hashes['train'][h], hashes['val'][h]] for h in sorted(duplicates)]
    if duplicates:
        report['warnings'].append('Exact duplicate image bytes across splits; review before training')
    output = ROOT / 'reports/uiis-audit.json'
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'errors': len(report['errors']), 'warnings': report['warnings']}, indent=2))
    assert not report['errors'], 'Dataset audit found errors; see report'
    print('UIIS_AUDIT_OK', flush=True)


if __name__ == '__main__':
    main()
