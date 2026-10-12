"""Wait for successful first epoch, validate it, then run the remaining budget once."""
import argparse
import fcntl
import json
import math
import subprocess
import sys
import time
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'work_dirs/uiis_baseline_r50_36e'
STATUS = ROOT / 'reports/overnight-status.json'


def status(state, **details):
    payload = dict(state=state, time=time.strftime('%Y-%m-%d %H:%M:%S'), **details)
    temporary = STATUS.with_suffix('.tmp')
    temporary.write_text(json.dumps(payload, indent=2))
    temporary.replace(STATUS)
    print(json.dumps(payload), flush=True)


def validate(report, checkpoint, expected_steps, verification):
    if (report['stage'] != 'first' or report['verification'] != verification
            or report['completed_epochs'] != 1 or report['completed_iterations'] != expected_steps):
        raise ValueError('First-epoch report does not match the agreed training stage')
    saved = torch.load(checkpoint, map_location='cpu')
    if saved['meta']['epoch'] != 1 or saved['meta']['iter'] != expected_steps:
        raise ValueError('Checkpoint progress does not match first epoch')
    if not saved.get('optimizer', {}).get('state') or not saved.get('param_schedulers'):
        raise ValueError('Checkpoint missing optimizer or scheduler state')
    for name, value in saved['state_dict'].items():
        if torch.is_tensor(value) and not torch.isfinite(value).all():
            raise ValueError(f'Nonfinite model state: {name}')
    for entry in saved['optimizer']['state'].values():
        for value in entry.values():
            if torch.is_tensor(value) and not torch.isfinite(value).all():
                raise ValueError('Nonfinite optimizer state')
    losses = [float(v.current()) for k, v in saved['message_hub']['log_scalars'].items()
              if k.startswith('train/') and 'loss' in k]
    if not losses or not all(math.isfinite(v) for v in losses):
        raise ValueError('Nonfinite or missing checkpoint losses')


def self_test():
    prior = json.loads((ROOT / 'reports/training-entry-verification.json').read_text())
    work = Path(prior['work_dir'])
    report = json.loads((work / 'result-first.json').read_text())
    checkpoint = work / 'milestones/epoch_1.pth'
    validate(report, checkpoint, 2, True)
    try:
        validate(dict(report, completed_epochs=2), checkpoint, 2, True)
    except ValueError:
        pass
    else:
        raise AssertionError('Invalid stage accepted')
    try:
        validate(report, checkpoint, 1969, False)
    except ValueError:
        pass
    else:
        raise AssertionError('Verification run accepted as formal run')
    print('OVERNIGHT_GATE_TEST_OK', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    with (ROOT / 'work_dirs/overnight-supervisor.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit('Overnight supervisor already running')
        if STATUS.exists() and json.loads(STATUS.read_text())['state'] in ('resuming', 'completed', 'resume_failed'):
            raise SystemExit('Continuation already attempted; inspect before restarting')
        status('waiting_for_first_epoch', timeout_minutes=120)
        deadline = time.monotonic() + 7200
        while True:
            result = (ROOT / 'reports/training-exit-code.txt').read_text().strip()
            if result == 'EXIT_CODE=0 action=first':
                sessions = subprocess.run(['screen', '-ls'], capture_output=True, text=True).stdout
                if '.uiis-training\t' not in sessions and '.uiis-training ' not in sessions:
                    break
            elif result != 'RUNNING first':
                raise RuntimeError(f'First stage not successful or changed unexpectedly: {result}')
            if time.monotonic() > deadline:
                raise TimeoutError('First epoch gate timed out; no automatic resume')
            time.sleep(15)
        report = json.loads((WORK / 'result-first.json').read_text())
        checkpoint = WORK / 'epoch_1.pth'
        latest = Path((WORK / 'last_checkpoint').read_text().strip()).resolve()
        if latest != checkpoint or Path(report['checkpoint']) != checkpoint:
            raise ValueError('First-epoch checkpoint paths do not match')
        validate(report, checkpoint, 1969, False)
        status('resuming', checkpoint=str(checkpoint), target_total_epochs=36)
        # Remain in this detached screen session for the full continuation.
        result = subprocess.run(['bash', 'scripts/training-worker.sh', 'resume'], cwd=ROOT)
        if result.returncode:
            status('resume_failed', exit_code=result.returncode)
            raise SystemExit(result.returncode)
        final = json.loads((WORK / 'result-resume.json').read_text())
        if final['completed_epochs'] != 36 or final['completed_iterations'] != 36 * 1969:
            raise RuntimeError('Continuation returned without completing the agreed budget')
        status('completed', completed_epochs=36, checkpoint=final['checkpoint'])


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        status('blocked', error=str(error))
        raise
