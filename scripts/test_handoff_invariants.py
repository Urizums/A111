"""Negative checks for accidentally accepting a false handoff transition."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from verify_handoff import validate_phase, safe_path


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


if __name__=='__main__':unittest.main()
