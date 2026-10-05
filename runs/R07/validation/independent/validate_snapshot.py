import errno
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANDIDATE = Path('/workspace/scratch/73714494ad2f/forge-takeover-r07/runs/R07/candidate/C6/forge-agent-flow')
SCRIPT = CANDIDATE / 'scripts' / 'snapshot.py'

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def hash_file(path):
    return sha256(path.read_bytes())

def tree_bytes(root):
    result = {}
    for p in sorted(root.rglob('*')):
        rel = p.relative_to(root).as_posix()
        if p.is_symlink():
            result[rel] = {'type': 'symlink', 'target': os.readlink(p)}
        elif p.is_dir():
            result[rel] = {'type': 'dir'}
        elif p.is_file():
            data = p.read_bytes()
            result[rel] = {'type': 'file', 'size': len(data), 'sha256': sha256(data), 'bytes_hex': data.hex()}
    return result

def main():
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    sys.dont_write_bytecode = True
    candidate_hash_before = hash_file(SCRIPT)
    run_root = Path(tempfile.mkdtemp(prefix='snapshot-validation-', dir=HERE))
    source = run_root / 'original-materials'
    bundle = run_root / 'snapshot-bundle'
    restored = run_root / 'restored-fresh'
    source.mkdir()
    expected = {
        'binary.dat': bytes(range(256)) * 2 + b'\x00\xff\n\x80tail',
        'empty.dat': b'',
        'nested dir/雪 name.txt': b'\xef\xbb\xbfline one\r\n\x00line two\xff',
    }
    def files_match(root):
        if not root.exists() or not root.is_dir():
            return False
        entries = list(root.rglob('*'))
        files = {p.relative_to(root).as_posix(): p.read_bytes() for p in entries
                 if p.is_file() and not p.is_symlink()}
        if any(not p.is_dir() and not p.is_file() for p in entries):
            return False
        return set(files) == set(expected) and all(files[name] == data for name, data in expected.items())
    for name, data in expected.items():
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    outside = run_root / 'outside.bin'
    outside.write_bytes(b'outside sentinel')
    (source / 'linked.bin').symlink_to(outside)

    records = []
    raw_failures = []
    unexpected_failures = []
    def outcome(name, passed, observed, expected_text):
        rec = {'case': name, 'passed': bool(passed), 'observed': observed, 'expected': expected_text}
        records.append(rec)
        if not passed:
            unexpected_failures.append(rec.copy())
        return bool(passed)

    command_records = []
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    def cli(label, args, expected_code):
        cmd = [sys.executable, str(SCRIPT)] + list(args)
        result = subprocess.run(cmd, cwd=str(CANDIDATE), env=env, text=True, capture_output=True)
        rec = {'label': label, 'argv': cmd, 'cwd': str(CANDIDATE), 'returncode': result.returncode,
               'stdout': result.stdout, 'stderr': result.stderr, 'expected_returncode': expected_code}
        command_records.append(rec)
        outcome(label, result.returncode == expected_code,
                {'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr},
                {'returncode': expected_code})
        return result

    cli('help', ['--help'], 0)
    capture_args = ['capture', '--root', str(source), '--out', str(bundle)]
    for name in expected:
        capture_args += ['--path', name]
    capture_result = cli('capture_exact_original_bytes', capture_args, 0)
    if capture_result.returncode == 0:
        verify_result = cli('verify_captured_bytes', ['verify', str(bundle)], 0)
        manifest = json.loads((bundle / 'manifest.json').read_text())
        manifest_ok = manifest.get('schema') == 'forge-byte-snapshot/1' and len(manifest.get('files', [])) == len(expected)
        objects_ok = True
        for row in manifest.get('files', []):
            raw = (bundle / 'objects' / row['sha256']).read_bytes()
            name = row['path']
            objects_ok = objects_ok and name in expected and raw == expected[name]
            objects_ok = objects_ok and row['size_bytes'] == len(raw) and row['sha256'] == sha256(raw)
        outcome('independent_object_bytes_match_originals', manifest_ok and objects_ok,
                {'manifest_schema': manifest.get('schema'), 'manifest_files': len(manifest.get('files', [])),
                 'all_object_bytes_equal_original': objects_ok},
                {'schema': 'forge-byte-snapshot/1', 'file_count': len(expected), 'exact_bytes': True})
        restore_result = cli('restore_to_fresh_destination', ['restore', str(bundle), '--out', str(restored)], 0)
        restored_ok = restore_result.returncode == 0 and files_match(restored)
        outcome('fresh_restore_is_byte_faithful', restored_ok,
                {'destination_exists': restored.exists(), 'tree': tree_bytes(restored) if restored.exists() else {}},
                {'all_original_relative_paths_and_bytes_restored': True})
    else:
        outcome('independent_object_bytes_match_originals', False, 'capture failed; byte comparison unavailable', {'exact_bytes': True})
        outcome('fresh_restore_is_byte_faithful', False, 'capture failed; restore unavailable', {'all_original_relative_paths_and_bytes_restored': True})

    bad_capture = run_root / 'unsafe-capture'
    bad_capture_result = cli('capture_rejects_parent_traversal',
        ['capture', '--root', str(source), '--out', str(bad_capture), '--path', '../outside.bin'], 2)
    traversal_rejected = bad_capture_result.returncode == 2 and not bad_capture.exists()
    outcome('unsafe_source_path_rejected_without_bundle', traversal_rejected,
            {'returncode': bad_capture_result.returncode, 'stderr': bad_capture_result.stderr, 'bundle_created': bad_capture.exists()},
            {'returncode': 2, 'bundle_created': False})
    link_capture = run_root / 'symlink-capture'
    symlink_result = cli('capture_rejects_source_symlink',
        ['capture', '--root', str(source), '--out', str(link_capture), '--path', 'linked.bin'], 2)
    outcome('source_symlink_is_not_followed', symlink_result.returncode == 2 and not link_capture.exists(),
            {'returncode': symlink_result.returncode, 'stderr': symlink_result.stderr, 'bundle_created': link_capture.exists()},
            {'returncode': 2, 'bundle_created': False})

    if bundle.exists():
        unsafe_bundle = run_root / 'unsafe-manifest-bundle'
        shutil.copytree(bundle, unsafe_bundle)
        unsafe_manifest = json.loads((unsafe_bundle / 'manifest.json').read_text())
        unsafe_manifest['files'][0]['path'] = '../escape.bin'
        (unsafe_bundle / 'manifest.json').write_text(json.dumps(unsafe_manifest))
        unsafe_result = cli('verify_rejects_unsafe_manifest_path', ['verify', str(unsafe_bundle)], 2)
        outcome('unsafe_manifest_path_rejected', unsafe_result.returncode == 2,
                {'returncode': unsafe_result.returncode, 'stderr': unsafe_result.stderr}, {'returncode': 2})

        corrupt_bundle = run_root / 'corrupt-object-bundle'
        shutil.copytree(bundle, corrupt_bundle)
        original_manifest = json.loads((corrupt_bundle / 'manifest.json').read_text())
        object_path = corrupt_bundle / 'objects' / original_manifest['files'][0]['sha256']
        object_path.write_bytes(object_path.read_bytes() + b'corruption')
        corrupt_result = cli('verify_rejects_corrupt_stored_bytes', ['verify', str(corrupt_bundle)], 2)
        outcome('corrupt_stored_bytes_rejected', corrupt_result.returncode == 2,
                {'returncode': corrupt_result.returncode, 'stderr': corrupt_result.stderr}, {'returncode': 2})

    existing = run_root / 'existing-destination'
    existing.mkdir()
    (existing / 'preserve.txt').write_bytes(b'pre-existing sentinel\x00\xff')
    before_existing = tree_bytes(existing)
    existing_result = cli('restore_refuses_existing_destination', ['restore', str(bundle), '--out', str(existing)], 2)
    after_existing = tree_bytes(existing)
    outcome('existing_destination_is_untouched', existing_result.returncode == 2 and before_existing == after_existing,
            {'returncode': existing_result.returncode, 'stderr': existing_result.stderr,
             'before': before_existing, 'after': after_existing}, {'returncode': 2, 'tree_unchanged': True})

    sys.path.insert(0, str(SCRIPT.parent))
    spec = importlib.util.spec_from_file_location('snapshot_candidate_independent', SCRIPT)
    snapshot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(snapshot)

    def leftovers(dest):
        return sorted(p.name for p in dest.parent.glob('.' + dest.name + '.restore-*'))
    def exact_restore(dest):
        return files_match(dest)

    write_dest = run_root / 'write-failure-target'
    real_path_open = Path.open
    failure_message = None
    try:
        def fail_during_write(self, mode='r', *args, **kwargs):
            if mode == 'xb' and self.as_posix().endswith('/nested dir/雪 name.txt'):
                raise OSError(errno.ENOSPC, 'injected disk-full during staged file write')
            return real_path_open(self, mode, *args, **kwargs)
        Path.open = fail_during_write
        try:
            snapshot.restore(bundle, write_dest)
            failure_message = 'restore unexpectedly succeeded under injected write failure'
        except OSError as exc:
            failure_message = f'{type(exc).__name__}: {exc}'
            raw_failures.append({'case': 'injected_file_write_failure', 'observed_error': failure_message, 'expected': True})
    finally:
        Path.open = real_path_open
    write_clean = not write_dest.exists() and leftovers(write_dest) == []
    outcome('write_failure_leaves_no_partial_destination', write_clean,
            {'error': failure_message, 'final_destination_exists': write_dest.exists(), 'staging_leftovers': leftovers(write_dest)},
            {'final_destination_exists': False, 'staging_leftovers': []})
    try:
        retry_result = snapshot.restore(bundle, write_dest)
        retry_ok = retry_result.get('restored') == len(expected) and exact_restore(write_dest)
        outcome('write_failure_destination_can_be_retried', retry_ok,
                {'restore_result': retry_result, 'exact_bytes': exact_restore(write_dest)}, {'retry_succeeds': True, 'exact_bytes': True})
    except Exception as exc:
        outcome('write_failure_destination_can_be_retried', False, f'{type(exc).__name__}: {exc}', {'retry_succeeds': True})

    publish_dest = run_root / 'publish-failure-target'
    real_publish = snapshot.publish_directory
    failure_message = None
    try:
        def fail_publication(staging, destination):
            raise OSError(errno.EIO, 'injected publication failure')
        snapshot.publish_directory = fail_publication
        try:
            snapshot.restore(bundle, publish_dest)
            failure_message = 'restore unexpectedly succeeded under injected publication failure'
        except OSError as exc:
            failure_message = f'{type(exc).__name__}: {exc}'
            raw_failures.append({'case': 'injected_publication_failure', 'observed_error': failure_message, 'expected': True})
    finally:
        snapshot.publish_directory = real_publish
    publish_clean = not publish_dest.exists() and leftovers(publish_dest) == []
    outcome('publication_failure_leaves_no_partial_destination', publish_clean,
            {'error': failure_message, 'final_destination_exists': publish_dest.exists(), 'staging_leftovers': leftovers(publish_dest)},
            {'final_destination_exists': False, 'staging_leftovers': []})
    try:
        retry_result = snapshot.restore(bundle, publish_dest)
        retry_ok = retry_result.get('restored') == len(expected) and exact_restore(publish_dest)
        outcome('publication_failure_destination_can_be_retried', retry_ok,
                {'restore_result': retry_result, 'exact_bytes': exact_restore(publish_dest)}, {'retry_succeeds': True, 'exact_bytes': True})
    except Exception as exc:
        outcome('publication_failure_destination_can_be_retried', False, f'{type(exc).__name__}: {exc}', {'retry_succeeds': True})

    unsupported_dest = run_root / 'unsupported-publisher-target'
    actual_platform = snapshot.sys.platform
    unsupported_message = None
    try:
        snapshot.sys.platform = 'darwin'
        try:
            snapshot.restore(bundle, unsupported_dest)
            unsupported_message = 'restore unexpectedly succeeded with unsupported platform'
        except OSError as exc:
            unsupported_message = f'{type(exc).__name__}: {exc}'
            raw_failures.append({'case': 'unsupported_publisher_capability', 'observed_error': unsupported_message, 'expected': True})
    finally:
        snapshot.sys.platform = actual_platform
    explicit = unsupported_message is not None and 'requires Linux renameat2' in unsupported_message
    clean = not unsupported_dest.exists() and leftovers(unsupported_dest) == []
    outcome('unsupported_publishing_capability_is_explicit', explicit and clean,
            {'error': unsupported_message, 'explicit_error': explicit, 'final_destination_exists': unsupported_dest.exists(), 'staging_leftovers': leftovers(unsupported_dest)},
            {'error_mentions': 'requires Linux renameat2', 'final_destination_exists': False, 'staging_leftovers': []})
    try:
        retry_result = snapshot.restore(bundle, unsupported_dest)
        retry_ok = retry_result.get('restored') == len(expected) and exact_restore(unsupported_dest)
        outcome('unsupported_attempt_does_not_block_later_supported_retry', retry_ok,
                {'restore_result': retry_result, 'exact_bytes': exact_restore(unsupported_dest)}, {'retry_succeeds': True, 'exact_bytes': True})
    except Exception as exc:
        outcome('unsupported_attempt_does_not_block_later_supported_retry', False, f'{type(exc).__name__}: {exc}', {'retry_succeeds': True})

    candidate_hash_after = hash_file(SCRIPT)
    outcome('candidate_source_unchanged', candidate_hash_before == candidate_hash_after,
            {'path': str(SCRIPT), 'sha256_before': candidate_hash_before, 'sha256_after': candidate_hash_after},
            {'sha256_before_equals_after': True})

    (HERE / 'commands.jsonl').write_text(''.join(json.dumps(rec, ensure_ascii=False) + '\n' for rec in command_records))
    (HERE / 'outcomes.json').write_text(json.dumps({'cases': records, 'raw_failures': raw_failures,
        'unexpected_failures': unexpected_failures}, ensure_ascii=False, indent=2) + '\n')
    result = {
        'task': 'independent source-local acceptance of snapshot.py byte snapshot utility',
        'candidate': str(CANDIDATE),
        'candidate_files_hashed': [{'path': str(SCRIPT), 'sha256_before': candidate_hash_before, 'sha256_after': candidate_hash_after}],
        'commands_log': str(HERE / 'commands.jsonl'),
        'outcomes_file': str(HERE / 'outcomes.json'),
        'run_materials': str(run_root),
        'cases_passed': sum(1 for rec in records if rec['passed']),
        'cases_failed': sum(1 for rec in records if not rec['passed']),
        'raw_induced_failures': raw_failures,
        'unexpected_failures': unexpected_failures,
        'result': 'pass' if not unexpected_failures else 'fail',
        'scope_note': 'Source-local independent acceptance; no global performance claim.'
    }
    (HERE / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not unexpected_failures else 1

if __name__ == '__main__':
    raise SystemExit(main())
