"""Read-only, evidence-checked host driver snapshot; never permits a call."""
from pathlib import Path

import hostbridge as h
import hostcapacity as capacity


def deadline_view(state, observe_clock):
    config = state['config'].get('deadline')
    saved = (state.get('current') or {}).get('deadline')
    if not config:
        return {'configured': False, 'clock_status': 'not_configured'}
    view = {'configured': True, **config, 'started': bool(saved),
            'clock_status': 'not_started', 'elapsed_seconds': None,
            'remaining_seconds': None, 'cutoff_reached': None,
            'scope': 'local_wait_since_granted_spawn_claim'}
    if not saved:
        return view
    view.update(started_clock=saved['started_clock'],
                interrupt_claimed_action=saved.get('interrupt_claimed_action'),
                completion_observed_after_deadline=saved.get('completion_observed_after_deadline'))
    try:
        now = observe_clock()
        view['observed_clock'] = now
        if now['boot_id'] != saved['started_clock']['boot_id']:
            view['clock_status'] = 'changed_boot'
        elif now['monotonic_ns'] < saved['started_clock']['monotonic_ns']:
            view['clock_status'] = 'backwards'
        else:
            view.update(clock_status='same_boot',
                        elapsed_seconds=(now['monotonic_ns'] - saved['started_clock']['monotonic_ns']) / 1e9,
                        remaining_seconds=max(0, saved['deadline_monotonic_ns'] - now['monotonic_ns']) / 1e9,
                        cutoff_reached=now['monotonic_ns'] >= saved['deadline_monotonic_ns'])
    except (ValueError, OSError, KeyError, TypeError) as error:
        view.update(clock_status='unavailable', clock_error=str(error))
    return view


def describe(root, state, observe_clock):
    """Caller holds driver lock. Never recover a journal or write run records."""
    current = state.get('current')
    c = None
    transaction_pending = False
    bridge_phase = None
    if current:
        job = Path(current['job_dir'])
        with h.checkpoint_lock(state['config']['checkpoint']):
            transaction_pending = (job / 'pending.json').exists()
            if transaction_pending:
                bridge_phase = 'transaction_pending'
            elif (job / 'control.json').exists():
                c = h.checked_control(job)
                bridge_phase = c['phase']
            else:
                h.need(h.sha(state['config']['checkpoint']) == state['checkpoint_sha256'],
                       'Checkpoint moved before preparation; reconcile current owner')
                bridge_phase = 'not_prepared'

    pending = None
    if state['pending']:
        record = state['actions'][state['pending']]
        action = h.read(record['payload_ref']['path'])
        pending = {'action_id': state['pending'], 'kind': action['kind'], 'tool': action['tool'],
                   'status': record['status'], 'payload_ref': record['payload_ref'],
                   'ack_ref': record.get('ack_ref')}

    admission = None
    if state['config'].get('capacity'):
        binding = state['config']['capacity']
        with h.checkpoint_lock(binding['path']):
            registry = capacity.checked(binding)
            own = registry['allocations'].get(c['request']['job_id']) if c else None
            admission = {**capacity.summary(registry), 'own_slot': own['status'] if own else None}

    deadline = deadline_view(state, observe_clock)
    review_ack_validation = None
    if pending and pending['kind'] == 'review' and pending['status'] == 'ack_pending' and c and c['phase'] == 'received':
        with h.checkpoint_lock(state['config']['checkpoint']):
            try:
                h.commit_plan(Path(current['job_dir']), c, pending['ack_ref']['path'])
                review_ack_validation = {'status': 'valid'}
            except ValueError as error:
                review_ack_validation = {'status': 'unavailable' if h.has_io_cause(error) else 'invalid', 'error': str(error)}
            except OSError as error:
                review_ack_validation = {'status': 'unavailable', 'error': str(error)}
    step = 'resume_original_controller'
    if state['phase'] == 'completed':
        step = 'completed'
    elif state['phase'] != 'active':
        step = 'explicit_reconciliation'
    elif transaction_pending:
        step = 'resume_saved_transaction'
    elif deadline['clock_status'] in {'changed_boot', 'backwards', 'unavailable'}:
        step = 'reconcile_clock'
    elif pending:
        if pending['status'] == 'ack_pending':
            step = ('reconcile_invalid_review_ack' if review_ack_validation and review_ack_validation['status'] == 'invalid'
                    else 'reconcile_review_evidence' if review_ack_validation and review_ack_validation['status'] == 'unavailable'
                    else 'replay_saved_ack')
        elif pending['status'] == 'proposed':
            step = ('wait_capacity' if pending['kind'] == 'spawn' and admission
                    and admission['available'] == 0 and admission['own_slot'] != 'held' else 'claim_pending_action')
        else:
            step = 'reconcile_claimed_action'
    elif bridge_phase in {'accepted', 'running', 'dispatching'}:
        step = 'query_bound_worker'
    elif bridge_phase == 'received':
        step = 'source_review'
    elif bridge_phase in {'committed', 'terminated', 'rejected'}:
        step = 'resume_terminal_record'

    return {'schema_version': 'forge-host-inspection/1', 'read_only': True,
            'automatic_host_call': False, 'call_allowed': False, 'execution_owner': 'host_agent',
            'run_id': state['run_id'], 'phase': state['phase'], 'reason': state['reason'],
            'driver_dir': str(root.resolve()), 'checkpoint': state['config']['checkpoint'],
            'closed_jobs': len(state['jobs']), 'current_target': current['target_id'] if current else None,
            'worker': (c['request']['host']['parent_task'] + '/' + c['request']['host']['task_name']) if c else None,
            'bridge_phase': bridge_phase, 'bridge_transaction_pending': transaction_pending,
            'bridge_validation': 'pending_recovery' if transaction_pending else 'verified' if c else 'not_prepared',
            'review_ack_validation': review_ack_validation,
            'pending_action': pending, 'next_required_step': step,
            'budgets': {'actions_claimed': state['claims'],
                        'actions_remaining': max(0, state['config']['max_actions'] - state['claims']),
                        'host_calls_claimed': state['host_call_claims'],
                        'current_polls_claimed': current['polls'] if current else None,
                        'current_polls_remaining': max(0, state['config']['max_polls_per_job'] - current['polls']) if current else None},
            'capacity': admission, 'deadline': deadline,
            'rejected_imports': len(state['rejected_imports']),
            'resume_run_id': state['run_id'], 'tokens': None, 'cost': None,
            'internal_model_identity_verified': False}
