"""Negative checks for accidentally accepting a false handoff transition."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from verify_handoff import validate_checkpoint, validate_phase, validate_continuation, safe_path


class HandoffInvariants(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'actual.json').write_text('{"exit_code":0}')
        def t(id, title, deps):
            return dict(id=id,title=title,owner='root',depends_on=deps,write_paths=['runs/'],
                        acceptance=['actual check'],status='planned',evidence=[],blocker=None,next_action=title)
        self.phase={'schema':'forge-phase-todo/1','phase_id':'P1','tasks':[
            t('a','work',[]), t('next','启动下一阶段任务',['a'])]}

    def test_ready_phase_allowed(self):
        self.assertEqual(validate_phase(self.phase, self.root), [])

    def test_cycle_rejected(self):
        self.phase['tasks'][0]['depends_on']=['next']
        self.assertTrue(any('cycle' in x for x in validate_phase(self.phase,self.root)))

    def test_unknown_dependency_rejected(self):
        self.phase['tasks'][0]['depends_on']=['missing']
        self.assertTrue(any('unknown dependency' in x for x in validate_phase(self.phase,self.root)))

    def test_false_transition_without_execution_rejected(self):
        for t in self.phase['tasks']:
            t.update(status='done',evidence=['actual.json'])
        self.phase['tasks'][-1]['transition']={'next_phase_id':'P2','todo_path':'next.json',
                                              'first_task_id':'a','start_evidence':[]}
        nxt=copy.deepcopy(self.phase);nxt['phase_id']='P2'
        nxt['tasks'][0].update(status='planned',evidence=[])
        (self.root/'next.json').write_text(json.dumps(nxt))
        errors=validate_phase(self.phase,self.root)
        self.assertTrue(any('actual-start' in x for x in errors))
        self.assertTrue(any('not actually started' in x for x in errors))

    def test_successor_bound_transition_allowed(self):
        for t in self.phase['tasks']:
            t.update(status='done',evidence=['actual.json'])
        nxt=copy.deepcopy(self.phase);nxt['phase_id']='P2'
        (self.root/'next.json').write_text(json.dumps(nxt))
        self.phase['tasks'][-1]['transition']={'next_phase_id':'P2','todo_path':'next.json',
                                              'first_task_id':'a','start_evidence':['actual.json']}
        self.assertEqual(validate_phase(self.phase,self.root),[])

    def test_path_escape_rejected(self):
        with self.assertRaises(ValueError): safe_path(self.root,'../escape')
        with self.assertRaises(ValueError): safe_path(self.root,'/tmp/escape')

    def test_transition_cannot_skip_prior_task(self):
        self.phase['tasks'][-1]['depends_on']=[]
        self.assertTrue(any('every earlier' in x for x in validate_phase(self.phase,self.root)))

    def test_done_without_evidence_rejected(self):
        self.phase['tasks'][0]['status']='done'
        self.assertTrue(any('done without evidence' in x for x in validate_phase(self.phase,self.root)))

    def test_historical_transition_resolves_archived_successor(self):
        for t in self.phase['tasks']:
            t.update(status='done', evidence=['actual.json'])
        successor=copy.deepcopy(self.phase);successor['phase_id']='P2'
        frontier=copy.deepcopy(successor);frontier['phase_id']='P3'
        (self.root/'state/history').mkdir(parents=True)
        (self.root/'state/phase-todo.json').write_text(json.dumps(frontier))
        (self.root/'state/history/P2-todo.json').write_text(json.dumps(successor))
        self.phase['tasks'][-1]['transition']={'next_phase_id':'P2','todo_path':'state/phase-todo.json',
                                             'first_task_id':'a','start_evidence':['actual.json']}
        self.assertEqual(validate_phase(self.phase,self.root), [])
        (self.root/'state/history/P2-todo.json').unlink()
        self.assertTrue(any('transition:' in e for e in validate_phase(self.phase,self.root)))

    def test_delivered_checkpoint_requires_terminal_phase_and_evidence(self):
        checkpoint=dict(active_phase='P1', next_task_id=None, lifecycle='delivered', delivery_evidence=['actual.json'])
        self.assertTrue(validate_checkpoint(checkpoint, self.phase))
        self.phase['tasks'][0]['status']='done'
        self.phase['tasks'][-1]['status']='cancelled'
        self.assertEqual(validate_checkpoint(checkpoint, self.phase), [])
        checkpoint['delivery_evidence']=[]
        self.assertTrue(validate_checkpoint(checkpoint, self.phase))

    def test_unfinished_checkpoint_cannot_select_no_task(self):
        self.assertTrue(validate_checkpoint(dict(active_phase='P1', next_task_id=None), self.phase))

    def test_delivery_cannot_hide_ready_continuation(self):
        task=dict(id='ready', queue='capabilities', category='test', priority=1,
                  owner='root', write_paths=['runs/'], acceptance=['real result'],
                  inputs=[], depends_on=[], status='planned', next_action='execute',
                  evidence=[], attempts=[], repairs_used=0, repair_limit=2, blocker=None)
        state=dict(project_goal=dict(status='active'),deliveries=dict(D00=dict(status='delivered')),
                   tasks=[task],execution={})
        checkpoint=dict(project_goal_status='active',next_queue_task_id=None,lifecycle='delivered')
        errors=validate_continuation(checkpoint,state,self.root)
        self.assertTrue(any('next queue task' in e for e in errors))
        self.assertTrue(any('must not terminate' in e for e in errors))
        checkpoint.update(next_queue_task_id='ready',lifecycle='active')
        self.assertEqual(validate_continuation(checkpoint,state,self.root),[])


if __name__=='__main__':unittest.main()
