"""Real install and benign path fixtures for the PR owner's delivery defects."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from delivery import source_files

ROOT = Path(__file__).resolve().parents[1]


class DeliveryPaths(unittest.TestCase):
    def fixture(self, manifest=False):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        root = base / 'checkout'
        (root / 'tracked').mkdir(parents=True)
        (root / 'tracked/config.txt').write_text('harmless local fixture\n')
        raw = (root / 'tracked/config.txt').read_bytes()
        row = dict(path='tracked/config.txt', size_bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        if manifest:
            (root / 'delivery-manifest.json').write_text(json.dumps(dict(files=[row])))
        else:
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            subprocess.run(['git', '-C', str(root), 'add', 'tracked/config.txt'], check=True)
        return root, base, row

    def test_regular_nested_file_supported_in_both_sources(self):
        for manifest in [False, True]:
            root, _, row = self.fixture(manifest)
            self.assertEqual(source_files(root), [row])

    def test_parent_symlink_outside_rejected_for_both_sources(self):
        for manifest in [False, True]:
            with self.subTest(manifest=manifest):
                root, base, _ = self.fixture(manifest)
                (root/'tracked').rename(base/'benign-external')
                (root/'tracked').symlink_to(base/'benign-external', target_is_directory=True)
                with self.assertRaises(ValueError):
                    source_files(root)

    def test_parent_symlink_inside_rejected_for_both_sources(self):
        for manifest in [False, True]:
            with self.subTest(manifest=manifest):
                root, _, _ = self.fixture(manifest)
                (root/'tracked').rename(root/'real')
                (root/'tracked').symlink_to(root/'real', target_is_directory=True)
                with self.assertRaises(ValueError):
                    source_files(root)

    def test_leaf_symlink_rejected_for_both_sources(self):
        for manifest in [False, True]:
            with self.subTest(manifest=manifest):
                root, base, _ = self.fixture(manifest)
                leaf = root/'tracked/config.txt'
                leaf.rename(base/'benign.txt')
                leaf.symlink_to(base/'benign.txt')
                with self.assertRaises(ValueError):
                    source_files(root)

    def test_manifest_itself_cannot_be_a_symlink(self):
        root, base, _ = self.fixture(True)
        manifest = root/'delivery-manifest.json'
        manifest.rename(base/'manifest.json')
        manifest.symlink_to(base/'manifest.json')
        with self.assertRaises(ValueError):
            source_files(root)

    def test_manifest_requires_canonical_relative_paths(self):
        for name in ['tracked/./config.txt', 'tracked//config.txt', './tracked/config.txt',
                     'tracked/../tracked/config.txt', '../benign.txt', '/tmp/benign.txt',
                     'C:\\benign.txt', '', 'tracked/config.txt/']:
            with self.subTest(path=name):
                root, _, row = self.fixture(True)
                row['path'] = name
                (root/'delivery-manifest.json').write_text(json.dumps(dict(files=[row])))
                with self.assertRaises(ValueError):
                    source_files(root)

    def test_manifest_duplicate_and_size_mismatch_rejected(self):
        root, _, row = self.fixture(True)
        (root/'delivery-manifest.json').write_text(json.dumps(dict(files=[row, row])))
        with self.assertRaises(ValueError):
            source_files(root)
        row['size_bytes'] += 1
        (root/'delivery-manifest.json').write_text(json.dumps(dict(files=[row])))
        with self.assertRaises(ValueError):
            source_files(root)


class InstalledRelease(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.prefix = Path(temp.name)/'install'
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.release = (self.prefix/'current').resolve()
        self.before = {name:(self.prefix/name).read_bytes() for name in ['deployment.json','bin/agent-forge']}
        self.link = os.readlink(self.prefix/'current')

    def install(self):
        return subprocess.run([sys.executable, '-B', str(ROOT/'scripts/deploy_cloud.py'),
                               '--prefix', str(self.prefix)], capture_output=True, text=True)

    def assert_unchanged(self):
        self.assertEqual(os.readlink(self.prefix/'current'), self.link)
        for name, raw in self.before.items():
            self.assertEqual((self.prefix/name).read_bytes(), raw)

    def test_extra_file_is_rejected_without_changing_active_install(self):
        extra = self.release/'unexpected.txt'
        extra.write_text('harmless drift fixture\n')
        result = self.install()
        self.assertNotEqual(result.returncode, 0, 'Drift was incorrectly reused')
        self.assert_unchanged()
        self.assertEqual(extra.read_text(), 'harmless drift fixture\n')

    def test_changed_or_missing_file_is_rejected(self):
        for operation in ['change', 'delete']:
            with self.subTest(operation=operation):
                target = self.release/'README.md'
                if operation == 'change':
                    target.write_text('harmless changed bytes\n')
                else:
                    target.unlink()
                self.assertNotEqual(self.install().returncode, 0)
                self.assert_unchanged()

    def test_symlink_replacing_release_file_is_rejected(self):
        target = self.release/'README.md'
        benign = self.prefix/'original-readme.txt'
        target.rename(benign)
        target.symlink_to(benign)
        self.assertNotEqual(self.install().returncode, 0)
        self.assert_unchanged()

    def test_empty_directory_drift_is_rejected(self):
        (self.release/'unexpected-empty').mkdir()
        self.assertNotEqual(self.install().returncode, 0)
        self.assert_unchanged()

    def test_cli_execution_then_reinstall_keeps_release_reusable(self):
        launcher = self.prefix/'bin/agent-forge'
        for args in [['verify','--json'], ['project','--help'], ['package','--help']]:
            result = subprocess.run([str(launcher), *args], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.install().returncode, 0)
        self.assertEqual(os.readlink(self.prefix/'current'), self.link)


if __name__ == '__main__':
    unittest.main()
