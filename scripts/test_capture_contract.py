"""Black-box checks of the new measurement recorder, including failed launches."""
import base64
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CAPTURE = Path(__file__).resolve().parents[1] / 'runs/S02/candidate/forge-agent-flow/scripts/capture.py'


class CaptureContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def run_capture(self, name, command):
        path = self.root / name
        result = subprocess.run([sys.executable, str(CAPTURE), 'cli', '--record', str(path),
                                 '--actor', 'worker', '--', *command], capture_output=True)
        return result, json.loads(path.read_text()) if path.exists() else None

    def test_raw_bytes_and_nonzero_exit(self):
        result, record = self.run_capture('raw.json', [sys.executable, '-c',
            'import os;os.write(1,bytes([255,0,10]));os.write(2,b"bad\\n");raise SystemExit(7)'])
        self.assertEqual(result.returncode, 7)
        self.assertEqual(base64.b64decode(record['stdout_base64']), b'\xff\x00\n')
        self.assertEqual(base64.b64decode(record['stderr_base64']), b'bad\n')
        self.assertEqual(record['exit_code'], 7)
        self.assertEqual(record['begin']['boot_id'], record['end']['boot_id'])
        self.assertGreaterEqual(record['end']['monotonic_ns'], record['begin']['monotonic_ns'])

    def test_missing_executable_is_recorded(self):
        result, record = self.run_capture('missing.json', [str(self.root / 'missing-executable')])
        self.assertIsNotNone(record, 'A failed launch must retain a command record')
        self.assertEqual(result.returncode, 127)
        self.assertEqual(record['exit_code'], 127)
        self.assertIn('No such file', record['stderr'])

    def test_existing_record_prevents_target_effect(self):
        effect = self.root / 'effect'
        command = [sys.executable, '-c', f'from pathlib import Path;Path({str(effect)!r}).write_text("once")']
        first, record = self.run_capture('only.json', command)
        before = (self.root / 'only.json').read_bytes()
        self.assertEqual(first.returncode, 0)
        effect.write_text('retained')
        second, _ = self.run_capture('only.json', command)
        self.assertNotEqual(second.returncode, 0)
        self.assertEqual(effect.read_text(), 'retained')
        self.assertEqual((self.root / 'only.json').read_bytes(), before)

    def test_successful_marker_target_is_captured(self):
        events = self.root / 'events'
        result, record = self.run_capture('mark.json', [sys.executable, str(CAPTURE), 'mark',
            '--events', str(events), '--actor', 'worker', '--stage', 'worker_work', '--event', 'begin'])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(record['exit_code'], 0)
        self.assertEqual(len(list(events.glob('*.json'))), 1)
        self.assertEqual(json.loads(next(events.glob('*.json')).read_text())['event'], 'begin')

    def test_invalid_marker_preserves_failure_without_event(self):
        events = self.root / 'events'
        result, record = self.run_capture('bad-mark.json', [sys.executable, str(CAPTURE), 'mark',
            '--events', str(events), '--actor', 'worker', '--stage', 'worker_work', '--event', 'invalid'])
        self.assertEqual(result.returncode, 2)
        self.assertEqual(record['exit_code'], 2)
        self.assertFalse(events.exists())


if __name__ == '__main__':
    unittest.main()
