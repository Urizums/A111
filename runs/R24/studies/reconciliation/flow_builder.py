#!/usr/bin/env python3
"""R24 adapter from one research case to existing Forge Flow IR v1.1.

Not a planner model, not a worker dispatcher, and not a security sandbox.
The target host must separately verify its actual capabilities and artifacts.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import stat
import tempfile
from pathlib import Path

SOURCE_FILES = ('brief.md', 'consumer.md', 'invoices.json', 'amendments.json', 'payments.json')

MAX_SOURCE_BYTES = 2 * 1024 * 1024


def verify_public_source(bundle: dict) -> dict:
    """Check on-disk source bytes immediately before/after consequential steps.

    This checks a local snapshot, not OS isolation or a protected persistent
    lease. Do not claim the flow controller itself enforces this guard.
    """
    errors = []
    if not isinstance(bundle, dict) or set(bundle) != {'base_path','source_sha256'}:
        return {'passed': False, 'errors': ['invalid source bundle shape']}
    base = Path(bundle['base_path'])
    expected = bundle['source_sha256']
    if not isinstance(expected, dict) or set(expected) != set(SOURCE_FILES):
        return {'passed': False, 'errors': ['source list does not match public case']}
    if not base.is_dir() or base.is_symlink():
        return {'passed': False, 'errors': ['source directory missing or symbolic link']}
    for name in SOURCE_FILES:
        file = base / name
        try:
            if file.is_symlink():
                errors.append(f'{name}: symbolic link not accepted')
                continue
            info = file.stat()
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_SOURCE_BYTES:
                errors.append(f'{name}: not a bounded regular file')
                continue
            if _hash(file) != expected[name]:
                errors.append(f'{name}: bytes no longer match frozen identity')
        except (OSError, TypeError, ValueError) as exc:
            errors.append(f'{name}: unable to verify: {exc}')
    return {'passed': not errors, 'errors': errors,
            'scope': 'local source guard; not authenticated host permission or OS isolation'}


def _hash(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _cap(name: str, effect: str, evidence: str | None) -> dict:
    # The absence of evidence is never silently interpreted as permission.
    return {'binding': name, 'effect': effect,
            'available': bool(evidence),
            'authorization': 'granted' if evidence else 'required',
            'evidence': evidence or 'No verified host receipt supplied; blocked.'}


def _node(name: str, kind: str, reads: list[str], writes: list[str],
          tool: str, prompt: str, checks: list[str], nxt: str) -> dict:
    return {'id': name, 'kind': kind, 'reads': reads, 'writes': writes,
            'tools': [tool], 'prompt': prompt, 'acceptance': checks,
            'max_visits': 1,
            'routes': {'ok': nxt, 'error': '$failed', 'blocked': '$blocked'},
            'emits': {'ok': writes, 'error': [], 'blocked': []}}


def make_flow(folder: Path, workspace_receipt: str | None = None) -> tuple[dict, dict]:
    folder = folder.resolve(strict=True)
    for name in SOURCE_FILES:
        if not (folder / name).is_file():
            raise ValueError(f'Missing neutral case source: {name}')
    # This is the *research case adapter*, not a general NLP classifier.
    # Read inputs before deciding what can be accepted.
    brief = (folder/'brief.md').read_text(encoding='utf-8')
    consumer = (folder/'consumer.md').read_text(encoding='utf-8')
    if 'ledger.csv' not in consumer or 'suppliers.csv' not in consumer:
        raise ValueError('The consumer contract does not identify both required outputs')
    for name in SOURCE_FILES[2:]:
        data = json.loads((folder/name).read_text(encoding='utf-8'))
        if not isinstance(data, list):
            raise ValueError(f'{name} must contain an array of records')
    context = {'base_path': str(folder), 'source_sha256': {name: _hash(folder/name) for name in SOURCE_FILES}}
    verified = verify_public_source(context)
    if not verified['passed']:
        raise ValueError('Public source could not be frozen safely: ' + '; '.join(verified['errors']))
    goal = 'Reconcile invoice and supplier balances as-of the brief; hand off usable method.'
    inputs = {
        'request': {'type': 'string', 'description': 'Original business request and consumer terms.'},
        'source_bundle': {'type': 'object', 'description': 'Public raw-source paths and frozen SHA-256 identities.'}}
    arts = {
        'tables': {'type': 'object', 'description': 'Real ledger.csv and suppliers.csv paths, plus workflow.md path.'},
        'audit': {'type': 'object', 'description': 'Observed numerical receiving checks and actual receipt paths.'},
        'delivery': {'type': 'object', 'description': 'Independent consumer receipt and final validated artifact pointers.'}}
    nodes = [
        _node('produce', 'agent', ['request', 'source_bundle'], ['tables'], 'workspace',
              'From the raw source and the downstream contract, compute every invoice and every supplier as of the stated cutoff. '
              'Write ledger.csv and suppliers.csv with the requested interface. Write workflow.md as an executable handoff in clear prose. '
              'Do not use a private oracle; report actual file identities and failures.',
              ['Both CSV files exist and have complete schema coverage.',
               'The handoff explains source versions, cutoff, calculation, and an error/refresh path.'], 'audit_data'),
        _node('audit_data', 'check', ['source_bundle', 'tables'], ['audit'], 'workspace',
              'Recompute or independently check the original public source. Verify source hash, effective approved amendments, '
              'posted payments by cutoff, signed integer cents, all invoices and all suppliers including zero balances. '
              'Do not report a workflow.md file as proof that its instructions can be reused.',
              ['Audit uses actual raw inputs and actual CSV contents.',
               'If any required row or numerical condition fails, do not route ok.'], 'receive_handoff'),
        _node('receive_handoff', 'check', ['request', 'source_bundle', 'tables', 'audit'], ['delivery'], 'receiver',
              'As a genuinely separate receiving context, read only the original business requirements, public raw data and deliverables. '
              'Cold-start reproduce the reconciliation from workflow.md without seeing author diagnoses or private oracle; '
              'check that this procedure makes the next action and failure handling understandable. '
              'Only issue ok with real replay receipts; otherwise report blocked or error.',
              ['A genuine independent recipient executed or replayed the handoff.',
               'All original mandatory outputs and correct meaning survived the handoff.',
               'Information leakage and missing host capability have not been disguised as acceptance.'], '$done')]
    spec = {'schema_version': '1.1', 'id': 'r24_reconcile_handoff', 'goal': goal,
            'assumptions': ['This case supplies synthetic USD-cent values and UTC ISO timestamps.',
                            'No new external transfers or payment mutations are authorized.'],
            'inputs': inputs, 'artifacts': arts, 'outputs': ['delivery'],
            'capabilities': {'workspace': _cap('local_file_execution', 'local_write', workspace_receipt),
                             'receiver': _cap('independent_receiving_context', 'read', None)},
            'budgets': {'max_steps': 3}, 'entry': 'produce', 'nodes': nodes}
    start_inputs = {'request': brief + '\n\n' + consumer, 'source_bundle': context}
    return spec, start_inputs


def inspect(spec: dict, inp: dict) -> dict:
    """Subset sanity check, not a substitute for repo's real flowctl.validate."""
    errors = []
    ids = [n['id'] for n in spec['nodes']]
    for n in spec['nodes']:
        for name in n['reads']:
            if name not in spec['inputs'] and name not in spec['artifacts']:
                errors.append(f'Unknown artifact read: {name}')
        for name in n['writes']:
            if name not in spec['artifacts']:
                errors.append(f'Undeclared produced artifact: {name}')
        for route in n['routes'].values():
            if route not in ids and route not in ('$done', '$blocked', '$failed'):
                errors.append(f'Unknown route: {route}')
        if n['emits']['ok'] != n['writes']:
            errors.append(f'Node {n["id"]} has inconsistent success outputs')
    if set(inp) != set(spec['inputs']):
        errors.append('Initial inputs missing or unexpected')
    if spec['nodes'][-1]['routes']['ok'] != '$done':
        errors.append('Missing completion route')
    if any(x not in spec['artifacts'] for x in spec['outputs']):
        errors.append('Final output not declared')
    return {'passed': not errors, 'errors': errors,
            'scope': 'local shape sanity; run existing flowctl.py validate in repository for full IR validation'}


def selftest() -> dict:
    # Deliberately reuse original generator only to make public input fixture;
    # we do not inspect or use private expected answers as producer evidence.
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from rehearsal import generate
    results = []
    def check(name, ok):
        results.append({'name': name, 'passed': bool(ok)})
    with tempfile.TemporaryDirectory() as t:
        pub = Path(t)/'case'
        generate(772, pub)
        source = pub/'producer'
        spec, inp = make_flow(source)
        check('local Flow shape sanity', inspect(spec, inp)['passed'])
        check('unverified workspace blocks dispatch by default', not spec['capabilities']['workspace']['available'])
        check('unverified acceptor blocks independent completion', not spec['capabilities']['receiver']['available'])
        check('every required stage yields real declared artifacts',
              [n['writes'] for n in spec['nodes']] == [['tables'], ['audit'], ['delivery']])
        check('flow does not claim execution on construction', 'status' not in spec and 'trace' not in spec)
        cap_spec, _ = make_flow(source, workspace_receipt='Actual local Python 3.13 run: case generation')
        check('workspace can be attested without inventing independent actor',
              cap_spec['capabilities']['workspace']['available'] and not cap_spec['capabilities']['receiver']['available'])
        original=(source/'payments.json').read_bytes()
        (source/'payments.json').write_bytes(original+b' ')
        _,after=make_flow(source)
        check('source revisions change frozen flow input identity',
              inp['source_bundle']['source_sha256']['payments.json'] != after['source_bundle']['source_sha256']['payments.json'])
        check('original bundle rejects mutated source before dispatch',
              not verify_public_source(inp['source_bundle'])['passed'])
        (source/'payments.json').write_bytes(original)
        check('source restoration restores frozen identity',make_flow(source)[1]['source_bundle']==inp['source_bundle'])
        check('source guard permits byte-identical restoration',verify_public_source(inp['source_bundle'])['passed'])
        (source/'payments.json').rename(source/'payments.backup')
        (source/'payments.json').symlink_to(source/'payments.backup')
        check('source guard rejects symbolic source files',not verify_public_source(inp['source_bundle'])['passed'])
        (source/'payments.json').unlink()
        (source/'payments.backup').rename(source/'payments.json')
        (source/'suppliers.csv').write_text('fake',encoding='utf-8')
        check('added file does not silently become required input',make_flow(source)[1]['source_bundle']==inp['source_bundle'])
    return {'passed': all(r['passed'] for r in results), 'checks': results,
            'scope': 'deterministic adapter fixtures; not full native flowctl integration or LLM autonomy'}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='action', required=True)
    g=sub.add_parser('build');g.add_argument('--public',type=Path,required=True)
    g.add_argument('--out',type=Path,required=True)
    g.add_argument('--workspace-receipt', default=None)
    sub.add_parser('selftest')
    args=p.parse_args(argv)
    try:
        if args.action=='selftest':
            result=selftest()
        else:
            if args.out.exists():
                raise FileExistsError('Output dir already exists; preserve existing version')
            flow, inp=make_flow(args.public,args.workspace_receipt)
            result=inspect(flow,inp)
            if result['passed']:
                args.out.mkdir(parents=True)
                for filename,data in [('flow.json',flow),('inputs.json',inp)]:
                    (args.out/filename).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
                result.update({'flow':str(args.out/'flow.json'),'inputs':str(args.out/'inputs.json'),
                               'capability_evidence':'operator statements, not authenticated provider receipts'})
    except (OSError,ValueError,TypeError,KeyError) as exc:
        result={'passed':False,'errors':[f'{type(exc).__name__}: {exc}']}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
