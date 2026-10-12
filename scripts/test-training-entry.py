"""Exercise actual model, checkpoints, resume, retention and project lock on 4 images."""
import fcntl
import json
import subprocess
import sys
import time
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]


def main():
    work = ROOT / 'work_dirs' / ('entry_verification_' + time.strftime('%Y%m%d_%H%M%S'))
    command = [sys.executable, str(ROOT / 'scripts/train-uiis.py'), '--work-dir', str(work), '--verification']
    (ROOT / 'work_dirs').mkdir(exist_ok=True)
    with (ROOT / 'work_dirs/uiis-training.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        duplicate = subprocess.run(command + ['--stage', 'first'], capture_output=True, text=True)
        assert duplicate.returncode != 0 and 'TRAINING_ALREADY_RUNNING' in duplicate.stderr
    subprocess.run(command + ['--stage', 'first'], check=True)
    first = json.loads((work / 'result-first.json').read_text())
    assert first['completed_epochs'] == 1 and first['completed_iterations'] == 2
    subprocess.run(command + ['--stage', 'resume'], check=True)
    resumed = json.loads((work / 'result-resume.json').read_text())
    assert resumed['resume_state_verified'] and resumed['completed_iterations'] == 10
    assert sorted(p.name for p in work.glob('epoch_*.pth')) == ['epoch_3.pth', 'epoch_4.pth', 'epoch_5.pth']
    assert sorted(p.name for p in (work / 'milestones').glob('*.pth')) == ['epoch_1.pth', 'epoch_3.pth', 'epoch_5.pth']
    saved = torch.load(work / 'epoch_5.pth', map_location='cpu')
    assert saved['meta']['epoch'] == 5 and saved['meta']['iter'] == 10
    assert len(saved['optimizer']['state']) > 0 and saved['param_schedulers']
    assert abs(max(resumed['optimizer_lrs']) - 1e-6) < 1e-10
    overwrite = subprocess.run(command + ['--stage', 'first'], capture_output=True, text=True)
    assert overwrite.returncode != 0 and 'Refusing to overwrite' in overwrite.stderr
    report = dict(passed=True, work_dir=str(work), first=first, resumed=resumed,
                  checks=['duplicate lock', 'first epoch gate', 'optimizer/scheduler exact restore',
                          '5 mini epochs complete', 'latest 3 retention', 'milestone archives',
                          'learning rate decay', 'existing run overwrite rejected'],
                  limitation='4 images, 2 steps per mini epoch; not a full UIIS epoch or formal training')
    (ROOT / 'reports/training-entry-verification.json').write_text(json.dumps(report, indent=2))
    print('TRAINING_ENTRY_VERIFICATION_OK', flush=True)


if __name__ == '__main__':
    main()
