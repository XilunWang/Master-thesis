"""Download the author's original UIIS files at a fixed HF revision; verify hashes."""
import concurrent.futures
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import threading

import requests

ROOT = Path(os.path.abspath(__file__)).parents[1] / 'data/UIIS'
API = 'https://huggingface.co/api/datasets/LiamLian0727/UIIS'
REPO = 'https://huggingface.co/datasets/LiamLian0727/UIIS'
LOCAL = threading.local()


def get(url):
    if not hasattr(LOCAL, 'session'):
        LOCAL.session = requests.Session()
    for attempt in range(4):
        try:
            response = LOCAL.session.get(url, timeout=(15, 90))
            if response.status_code == 429 and attempt < 3:
                delay = response.headers.get('Retry-After', '60')
                time.sleep(max(60, int(delay)) if delay.isdigit() else 60)
                continue
            response.raise_for_status()
            return response
        except requests.RequestException:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def valid(path, item):
    if not path.is_file() or path.stat().st_size != item['size']:
        return False
    content = path.read_bytes()
    if item.get('lfs'):
        return hashlib.sha256(content).hexdigest() == item['lfs']['oid']
    return hashlib.sha1(('blob %d\0' % len(content)).encode() + content).hexdigest() == item['oid']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mirror', action='store_true', help='Use hf-mirror.com for file transport; official manifest hashes still required')
    parser.add_argument('--audit-only', action='store_true', help='Check local hashes without network; write missing-files.json')
    parser.add_argument('--workers', type=int, default=8, help='Concurrent downloads (1-24)')
    args = parser.parse_args()
    download_repo = REPO.replace('huggingface.co', 'hf-mirror.com') if args.mirror else REPO
    ROOT.mkdir(parents=True, exist_ok=True)
    manifest_path = ROOT / 'download-manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
    else:
        revision = get(API).json()['sha']
        url = API + '/tree/' + revision + '?recursive=true&limit=1000'
        files = []
        while url:
            response = get(url)
            files.extend(i for i in response.json() if i['type'] == 'file'
                         and (i['path'].startswith(('train/', 'val/', 'annotations/'))
                              or i['path'] == 'README.md'))
            url = response.links.get('next', {}).get('url')
        manifest = {'source': REPO, 'revision': revision, 'files': files}
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    files = manifest['files']
    print('Revision:', manifest['revision'], 'Files:', len(files), flush=True)
    if args.audit_only:
        missing = [item['path'] for item in files if not valid(ROOT / item['path'], item)]
        (ROOT / 'missing-files.json').write_text(json.dumps(missing), encoding='utf-8')
        print('Missing or invalid:', len(missing), flush=True)
        if missing:
            raise SystemExit(1)
        print('UIIS_DOWNLOAD_OK', flush=True)
        return

    def download(item):
        dest = ROOT / item['path']
        if '..' in Path(item['path']).parts or Path(item['path']).is_absolute():
            raise ValueError('Unsafe dataset path')
        if valid(dest, item):
            return
        dest.parent.mkdir(parents=True, exist_ok=True)
        response = get(download_repo + '/resolve/' + manifest['revision'] + '/' + item['path'])
        temp = dest.with_name(dest.name + '.part')
        with temp.open('wb') as target:
            for offset in range(0, len(response.content), 65536):
                target.write(response.content[offset:offset + 65536])
        if not valid(temp, item):
            raise ValueError('Hash mismatch: ' + item['path'])
        temp.replace(dest)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(args.workers, 24))) as pool:
        futures = [pool.submit(download, item) for item in files]
        errors = []
        for index, future in enumerate(concurrent.futures.as_completed(futures), 1):
            try:
                future.result()
            except Exception as error:
                errors.append(str(error))
                print('DOWNLOAD_ERROR:', str(error), flush=True)
            if index % 100 == 0 or index == len(files):
                print('Processed %d/%d; errors=%d' % (index, len(files), len(errors)), flush=True)
    if errors:
        raise RuntimeError('Download incomplete: ' + repr(errors))
    print('UIIS_DOWNLOAD_OK', flush=True)


if __name__ == '__main__':
    main()
