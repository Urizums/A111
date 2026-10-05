#!/usr/bin/env python3
"""Incomplete host protocol drafts and read-only preflight; no tool calls/commit."""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import re

import forge_template as templates
import hostbridge as bridge
import projectctl


def need(condition, message):
    if not condition:
        raise templates.TemplateError(message)


def request_context(path):
    envelope = templates.load_json(path)
    need(isinstance(envelope, dict) and set(envelope) == {'request', 'request_hash'}, 'Expected original prepared host request envelope')
    request = envelope['request']
    need(isinstance(request, dict) and request.get('schema_version') == 'forge-host-request/1', 'Unsupported host request schema')
    need(envelope['request_hash'] == bridge.digest(request), 'Request binding mismatch; restore original request')
    need(request.get('kind') in {'project', 'package'}, 'Unsupported request kind')
    for name in ['job_id', 'attempt_id', 'invocation_id']:
        need(isinstance(request.get(name), str) and bool(request[name].strip()), 'Missing request identity: '+name)
    work = request.get('work')
    need(isinstance(work, dict) and {'prompt','inputs','write_paths','reply_path','input_files'} <= set(work), 'Malformed prepared work')
    need(isinstance(work['write_paths'], list) and bool(work['write_paths']), 'Missing worker scopes')
    for scope in work['write_paths']:
        need(isinstance(scope, str) and Path(scope).is_absolute(), 'Worker scopes must be absolute')
    need(isinstance(work['reply_path'], str) and Path(work['reply_path']).is_absolute(), 'Assigned reply path must be absolute')
    scopes = [Path(p).resolve() for p in work['write_paths']]
    need(any(Path(work['reply_path']).resolve().is_relative_to(p) for p in scopes), 'Assigned reply path outside worker scope')
    refs = work['input_files']
    need(isinstance(refs, list), 'Input references must be a list')
    for ref in refs:
        need(isinstance(ref, dict) and set(ref) == {'path','sha256'} and isinstance(ref['path'], str)
             and Path(ref['path']).is_absolute(), 'Input reference needs absolute path and SHA/intentional absence')
        need(ref['sha256'] is None or (isinstance(ref['sha256'], str) and re.fullmatch('[0-9a-f]{64}',ref['sha256'])), 'Invalid input SHA')
        need(not any(Path(ref['path']).resolve().is_relative_to(scope) for scope in scopes), 'Worker scope includes bound input')
    need(not any(Path(path).resolve().is_relative_to(scope) for scope in scopes), 'Worker scope includes immutable request')
    bridge.check_refs(refs)
    return {'request': request, 'request_hash': envelope['request_hash']}


def artifact_refs(context, paths):
    work = context['request']['work']
    scopes = [Path(p).resolve() for p in work['write_paths']]
    result = []
    for path in paths:
        resolved = Path(path).resolve(strict=True)
        need(resolved.is_file(), 'Artifact must be an existing regular file')
        need(any(resolved.is_relative_to(scope) for scope in scopes), 'Artifact outside assigned worker scope')
        need(resolved != Path(work['reply_path']).resolve(), 'Artifact cannot reference the reply itself')
        ref = bridge.reference(resolved)
        need(ref not in result, 'Duplicate artifact path')
        result.append(ref)
    return result


def reply_draft(request_path, artifacts=(), flow_outcome=None):
    context = request_context(request_path)
    request = context['request']
    result = None
    if request['kind'] == 'package':
        dispatch = request.get('dispatch')
        templates._validate_dispatch(dispatch)
        need(dispatch['invocation_id'] == request['invocation_id'], 'Package invocation binding mismatch')
        result = ({'invocation_id': request['invocation_id'], 'outcome': None, 'artifacts': {}, 'evidence': []}
                  if flow_outcome is None else templates.make_response_draft(dispatch, flow_outcome))
    else:
        need(flow_outcome is None, 'Flow outcome applies only to a package request')
    return {'schema_version': 'forge-host-reply/1', 'job_id': request['job_id'],
            'attempt_id': request['attempt_id'], 'request_hash': context['request_hash'],
            'outcome': None, 'result': result, 'artifacts': artifact_refs(context, artifacts), 'reason': None}


def received_context(job):
    job = Path(job).resolve(strict=True)
    context = bridge.checked_control(job)
    need(context['phase'] == 'received', 'Decision requires an original received, uncommitted bridge')
    return job, context


def decision_draft(job, evidence=()):
    job, context = received_context(job)
    candidates = [bridge.reference(path) for path in evidence]
    if context['request']['kind'] == 'project':
        state = projectctl.load_state(context['target'])
        task_id = context['request']['target_binding']['task_id']
        task = next(item for item in state['plan']['tasks'] if item['id'] == task_id)
        definitions = {item['id']: item for item in state['plan']['acceptance']}
        results = {'acceptance_results': {aid: {'status':'not_run', 'level': definitions[aid]['level'],
                    'evidence': deepcopy(candidates)} for aid in task['acceptance_ids']}}
        lock = state.get('evaluation_plan_lock')
        if lock is not None:
            results['evaluation_plan_hash'] = lock['plan_hash']
    else:
        need(not candidates, 'Package evidence belongs in the actual worker Flow response; do not modify it here')
        results = deepcopy(templates.load_json(context['reply_ref']['path'])['result'])
    return {'schema_version': 'forge-host-decision/1', 'request_hash': context['request_hash'],
            'reply_sha256': context['reply_ref']['sha256'], 'outcome': None, 'results': results, 'reason': None}


def write_reply(request_path, out, artifacts=(), flow_outcome=None):
    context = request_context(request_path)
    destination = Path(out).resolve()
    scopes = [Path(p).resolve() for p in context['request']['work']['write_paths']]
    need(any(destination.is_relative_to(p) for p in scopes), 'Reply draft output outside worker scope')
    draft = reply_draft(request_path, artifacts, flow_outcome)
    inputs = [request_path, *artifacts, *[r['path'] for r in context['request']['work']['input_files']]]
    templates._write_exclusive_json(out, draft, inputs)
    return draft


def write_decision(job, out, evidence=()):
    job, context = received_context(job)
    destination = Path(out).resolve()
    need(not destination.is_relative_to(job), 'Decision draft output cannot be bridge metadata')
    protected = [context['target'], *[r['path'] for r in context['refs']],
                 *[r['path'] for r in context['request']['work']['input_files']], *evidence]
    if context['package_ref']:
        protected.append(context['package_ref']['path'])
    draft = decision_draft(job, evidence)
    templates._write_exclusive_json(out, draft, protected)
    return draft


def check_reply(request_path, reply_path):
    context = request_context(request_path)
    reply = templates.load_json(reply_path)
    bridge.check_reply_identity(context, reply_path, reply)
    bridge.check_reply_content(context, reply)
    return {'status': 'payload_valid', 'read_only': True, 'automatic_host_call': False,
            'call_allowed': False, 'native_completion_checked': False, 'semantic_acceptance': 'not_evaluated',
            'scope': 'existing outer host reply and file refs only; original receive/commit remain required'}


def check_decision(job, decision_path):
    job, context = received_context(job)
    templates.load_json(decision_path)
    bridge.commit_plan(job, context, decision_path)
    return {'status': 'controller_compatible', 'read_only': True, 'automatic_host_call': False,
            'call_allowed': False, 'committed': False, 'semantic_acceptance': 'not_evaluated',
            'scope': 'original controller validation and stored local refs; not independent semantic grading'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    reply = commands.add_parser('reply', help='write an explicitly incomplete host reply')
    reply.add_argument('--request', required=True)
    reply.add_argument('--artifact', action='append', default=[])
    reply.add_argument('--flow-outcome')
    reply.add_argument('--out', required=True)
    decision = commands.add_parser('decision', help='write ungraded original acceptance rows')
    decision.add_argument('--job', required=True)
    decision.add_argument('--evidence', action='append', default=[])
    decision.add_argument('--out', required=True)
    check = commands.add_parser('check-reply', help='read-only outer protocol preflight, not acceptance')
    check.add_argument('--request', required=True)
    check.add_argument('--reply', required=True)
    check = commands.add_parser('check-decision', help='read-only original controller preflight, no commit')
    check.add_argument('--job', required=True)
    check.add_argument('--decision', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'reply':
            write_reply(args.request, args.out, args.artifact, args.flow_outcome)
        elif args.command == 'decision':
            write_decision(args.job, args.out, args.evidence)
        elif args.command == 'check-reply':
            print(json.dumps(check_reply(args.request, args.reply), indent=2)); return 0
        else:
            print(json.dumps(check_decision(args.job, args.decision), indent=2)); return 0
        print(json.dumps({'status':'draft', 'out':str(Path(args.out).resolve()), 'ready_to_submit':False,
                          'automatic_host_call':False, 'call_allowed':False,
                          'next_action':'Fill actual work or independent review; preflight then use original receive/commit.'},indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, StopIteration) as error:
        print(json.dumps({'status':'unavailable' if bridge.has_io_cause(error) else 'invalid',
                          'error':str(error), 'read_only':args.command.startswith('check-'),
                          'automatic_host_call':False, 'call_allowed':False},indent=2))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
