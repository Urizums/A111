"""Reproduce advancing-frontier history validation against selected verifier."""
import importlib.util,json,sys,tempfile
from pathlib import Path
source=Path(sys.argv[1]).resolve();spec=importlib.util.spec_from_file_location('checker',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
with tempfile.TemporaryDirectory() as d:
 root=Path(d);(root/'state/history').mkdir(parents=True);(root/'evidence.json').write_text('{}')
 def task(id,title,deps):return dict(id=id,title=title,owner='root',depends_on=deps,write_paths=['runs/'],acceptance=['evidence'],status='done',evidence=['evidence.json'],blocker=None,next_action='retain')
 previous={'schema':'forge-phase-todo/1','phase_id':'S00','tasks':[task('a','work',[]),task('next','启动下一阶段任务',['a'])]}
 successor={'schema':'forge-phase-todo/1','phase_id':'S01','tasks':[task('first','work',[]),task('next','启动下一阶段任务',['first'])]}
 current=dict(successor,phase_id='S02')
 (root/'state/phase-todo.json').write_text(json.dumps(current));(root/'state/history/S01-todo.json').write_text(json.dumps(successor))
 previous['tasks'][-1]['transition']={'next_phase_id':'S01','todo_path':'state/phase-todo.json','first_task_id':'first','start_evidence':['evidence.json']}
 errors=module.validate_phase(previous,root);print(json.dumps({'ok':not errors,'errors':errors,'verifier':str(source)}));raise SystemExit(bool(errors))
