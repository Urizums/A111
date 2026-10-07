"""Behavioral guards for delivery/goal separation and evidence-bound continuation."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from continuation import advance, begin, finish, identity, ready, summary, validate, write_json, ref


class ContinuationCases(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'state/history').mkdir(parents=True)
        write_json(self.root/'step.json',dict(state='finished',argv=['python','real-step.py'],exit_code=0,
                                            begin={'utc':'start'},end={'utc':'end'},stdout='observed',stderr=''))
        (self.root/'input.txt').write_text('frozen new material')
        def task(id,queue,deps):
            return dict(id=id,queue=queue,category='test',priority=1,owner='root',write_paths=[id+'/'],
                        acceptance=[dict(id='result',assertion='Actual output is correct')],inputs=['input.txt'],
                        depends_on=deps,status='planned',next_action='execute',evidence=[],attempts=[],
                        repairs_used=0,repair_limit=2,blocker=None)
        self.state=dict(project_goal=dict(id='rd',status='active'),deliveries={'D00':dict(status='delivered')},
                        tasks=[task('a','capabilities',[]),task('b','challenges',[]),task('c','challenges',['a'])],
                        execution=dict(background_available=False))

    def result(self,id,status='pass',name='result.json'):
        t=next(t for t in self.state['tasks'] if t['id']==id)
        r=dict(task_id=id,attempt_id=t['attempts'][-1]['id'],requirements_hash=identity(t['acceptance']),
               criteria=[dict(id='result',status=status,evidence=['step.json'])],
               effect=dict(target='correct result',hypothesis='fixture',baseline='before',conditions='local',
                           observations='recorded',limits='not provider',metrics={'time_gain':None}))
        write_json(self.root/name,r)
        return name

    def test_delivery_does_not_close_goal_or_hide_ready_tasks(self):
        view=summary(self.state)
        self.assertEqual(view['project_goal']['status'],'active')
        self.assertEqual(view['next_task_id'],'a')
        self.assertEqual(view['ready_tasks'],['a','b'])

    def test_blocked_branch_does_not_block_independent_challenge(self):
        self.state['tasks'][0].update(status='blocked',blocker='Missing target; configure it.')
        self.assertEqual([t['id'] for t in ready(self.state)],['b'])

    def test_start_requires_actual_execution_and_ready_dependencies(self):
        write_json(self.root/'plan.json',dict(planned=True))
        with self.assertRaises(ValueError):begin(self.state,self.root,'a','plan.json')
        with self.assertRaises(ValueError):begin(self.state,self.root,'c','step.json')
        begin(self.state,self.root,'a','step.json')
        with self.assertRaises(ValueError):begin(self.state,self.root,'a','step.json')

    def test_reject_stale_acceptance_or_changed_input(self):
        begin(self.state,self.root,'a','step.json')
        result=self.result('a')
        original=copy.deepcopy(self.state)
        self.state['tasks'][0]['acceptance'][0]['assertion']='weakened'
        with self.assertRaises(ValueError):finish(self.state,self.root,'a',result)
        self.state=original
        (self.root/'input.txt').write_text('replacement sample')
        with self.assertRaises(ValueError):finish(self.state,self.root,'a',result)

    def test_failures_retained_and_repair_budget_cannot_reset(self):
        for n in range(3):
            begin(self.state,self.root,'a','step.json')
            finish(self.state,self.root,'a',self.result('a','fail','failure-'+str(n)+'.json'))
        task=self.state['tasks'][0]
        self.assertEqual(task['status'],'blocked')
        self.assertEqual(task['repairs_used'],2)
        self.assertEqual(len(task['attempts']),3)
        with self.assertRaises(ValueError):begin(self.state,self.root,'a','step.json')
        (self.root/'failure-0.json').unlink()
        self.assertTrue(validate(self.state,self.root))

    def test_missing_evidence_cannot_complete_task(self):
        begin(self.state,self.root,'a','step.json')
        result=self.result('a')
        (self.root/'step.json').unlink()
        with self.assertRaises(ValueError):finish(self.state,self.root,'a',result)

    def enable_progress_policy(self):
        (self.root/'user-policy.txt').write_text('Explicit current user policy amendment')
        self.state['tasks'][0].update(repair_limit=None, execution_policy=dict(
            mode='progress_guard', source=ref(self.root,'user-policy.txt'),
            progress_state='ready', deadline_utc=None,
            stop_conditions=['verified outcome', 'resource/authority boundary', 'unsupported repeated path']))

    def recovery(self, n):
        name='observation-'+str(n)+'.txt'
        (self.root/name).write_text('Observed defect '+str(n))
        self.state['tasks'][0]['recovery_note']=dict(observation='defect '+str(n),
            change_or_new_information='test a changed method for defect '+str(n),
            expected_check='original outcome assertion', evidence=[ref(self.root,name)])

    def test_progress_recovery_beyond_two_retains_all_failures(self):
        self.enable_progress_policy()
        for n in range(4):
            if n:self.recovery(n)
            begin(self.state,self.root,'a','step.json')
            finish(self.state,self.root,'a',self.result('a','fail','failure-'+str(n)+'.json'))
        task=self.state['tasks'][0]
        self.assertEqual(task['status'],'failed')
        self.assertEqual(task['repairs_used'],3)
        self.assertEqual(len(task['attempts']),4)
        self.assertFalse(validate(self.state,self.root))
        self.recovery(4)
        begin(self.state,self.root,'a','step.json')
        finish(self.state,self.root,'a',self.result('a','pass','verified.json'))
        self.assertEqual(task['status'],'done')
        self.assertEqual(task['repairs_used'],4)

    def test_progress_retry_requires_change_and_rejects_reused_rationale(self):
        self.enable_progress_policy()
        begin(self.state,self.root,'a','step.json')
        finish(self.state,self.root,'a',self.result('a','fail','first.json'))
        with self.assertRaises(ValueError):begin(self.state,self.root,'a','step.json')
        self.recovery(1)
        begin(self.state,self.root,'a','step.json')
        finish(self.state,self.root,'a',self.result('a','fail','second.json'))
        with self.assertRaises(ValueError):begin(self.state,self.root,'a','step.json')
        self.assertEqual(self.state['tasks'][0]['repairs_used'],1)

    def test_progress_policy_honors_actual_deadline_and_stalled_path(self):
        self.enable_progress_policy()
        task=self.state['tasks'][0]
        task['execution_policy']['deadline_utc']='1970-01-01T00:00:00+00:00'
        self.assertNotIn('a',[t['id'] for t in ready(self.state)])
        with self.assertRaises(ValueError):begin(self.state,self.root,'a','step.json')
        task['execution_policy']['deadline_utc']=None
        begin(self.state,self.root,'a','step.json')
        task['execution_policy']['progress_state']='stalled'
        finish(self.state,self.root,'a',self.result('a','fail','stalled.json'))
        self.assertEqual(task['status'],'blocked')
        self.assertIn('Progress guard',task['blocker'])
        self.assertEqual(task['repairs_used'],0)

    def test_progress_policy_cannot_weaken_criteria_or_ignore_drift(self):
        self.enable_progress_policy()
        begin(self.state,self.root,'a','step.json')
        result=self.result('a')
        self.state['tasks'][0]['acceptance'][0]['assertion']='weakened requirement'
        with self.assertRaises(ValueError):finish(self.state,self.root,'a',result)
        self.state['tasks'][0]['acceptance'][0]['assertion']='Actual output is correct'
        (self.root/'user-policy.txt').write_text('Unrecorded replacement policy')
        self.assertTrue(validate(self.state,self.root))

    def test_scope_overlap_defers_concurrent_writer(self):
        self.state['tasks'][1]['write_paths']=['a/child/']
        begin(self.state,self.root,'a','step.json')
        with self.assertRaises(ValueError):begin(self.state,self.root,'b','step.json')

    def test_next_phase_requires_real_first_step_and_preserves_old_phase(self):
        begin(self.state,self.root,'a','step.json')
        finish(self.state,self.root,'a',self.result('a'))
        def phase(name,id):
            return dict(schema='forge-phase-todo/1',phase_id=name,tasks=[
                dict(id=id,title='work',depends_on=[],status='planned',evidence=[]),
                dict(id=name+'-next',title='启动下一阶段任务',depends_on=[id],status='planned',evidence=[])])
        write_json(self.root/'state/phase-todo.json',phase('R1','a'))
        write_json(self.root/'state/next.json',phase('R2','c'))
        with self.assertRaises(ValueError):advance(self.root,self.state,'state/next.json')
        begin(self.state,self.root,'c','step.json')
        advance(self.root,self.state,'state/next.json')
        old=json.loads((self.root/'state/history/R1-todo.json').read_text())
        self.assertEqual(old['tasks'][-1]['status'],'done')
        self.assertTrue(old['tasks'][-1]['transition']['start_evidence'])


if __name__=='__main__':unittest.main()
