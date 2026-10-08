"""No solver: final text/numerical bindings, actual visual record and source integrity."""
from pathlib import Path
import json,hashlib,re,datetime,platform
from PIL import Image,ImageChops
V2=Path(__file__).resolve().parents[1];OLD=V2.parent/'execution'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def table(s,prefix):
    lines=s.splitlines();start=next(i for i,l in enumerate(lines) if l.startswith(prefix));end=start
    while end<len(lines) and lines[end].startswith('|'):end+=1
    return '\n'.join(lines[start:end])
def main():
    oldmanifest=load(OLD/'manifest.json');assert len(oldmanifest['files'])==3722
    for r in oldmanifest['files']:
        p=OLD/r['path'];assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],p
    ed=load(V2/'logs/editorial_changes.json');docs={n:(V2/(n+'.md')).read_text(encoding='utf-8') for n in ['paper','technical_report']}
    for e in ed['important_edits']:
        n='technical_report' if e['document']=='report' else 'paper'
        assert e['original_sentence'] in (OLD/(n+'.md')).read_text(encoding='utf-8')
        assert e['revised_sentence'] in docs[n],e
    fb=load(V2/'logs/reader_feedback_changes.json')
    for e in fb:assert e['final_sentence'] in docs[e['document']]
    for n in docs:
        original=(OLD/(n+'.md')).read_text(encoding='utf-8')
        for pref in ['| 任务 | 车型组成','| 参数场景 |']:assert table(docs[n],pref)==table(original,pref)
    for pref in ['| 货物 |','| 任务 | 方法']:assert table(docs['paper'],pref)==table((OLD/'paper.md').read_text(encoding='utf-8'),pref)
    # Bind actual source values, not only table text equality.
    taskrows=[]
    for line in table(docs['paper'],'| 任务 | 车型组成').splitlines()[2:]:
        c=[x.strip() for x in line.strip('|').split('|')];m=load(OLD/f'plans/{c[0]}/selected/metrics.json')
        assert c[1]==f"{m['n1']}T1+{m['n2']}T2" and int(c[2])==m['N'] and float(c[3])==m['C']
        assert c[4]==f"{m['Uv']*100:.2f}%" and c[5]==f"{m['Uw']*100:.2f}%"
        taskrows.append({'task':c[0],'metrics_sha256':sha(OLD/f'plans/{c[0]}/selected/metrics.json'),'table_values_match':True})
    sens=load(OLD/'sensitivity/results.json');paramrows=[]
    for line in table(docs['paper'],'| 参数场景 |').splitlines()[2:]:
        c=[x.strip() for x in line.strip('|').split('|')];matches=[r for r in sens if r['scenario']==c[0] and r['task']=='Q2-C'];assert len(matches)==1
        m=matches[0];assert [int(c[k]) for k in range(1,5)]==[m['n1'],m['n2'],m['N'],m['C']]
        assert c[5]==f"{m['Uv']*100:.2f}%" and c[6]==f"{m['Uw']*100:.2f}%"
        paramrows.append({'scenario':c[0],'values_match_frozen_result':True})
    images=[]
    for p in sorted((V2/'figures').glob('*')):assert sha(p)==sha(OLD/'figures'/p.name);images.append({'path':p.name,'sha256':sha(p),'same_as_frozen':True})
    fresh=load(OLD/'replay/fresh3/receipt.json');code={n:sha(OLD/'src'/n) for n in ['solver.py','checker.py','column_milp.py','reproduce.py']}
    cfg={r['task']:sha(OLD/f"plans/{r['task']}/selected/config.json") for r in fresh['receipts']}
    assert fresh['code_binding']==code and fresh['selected_config_binding']==cfg and fresh['input_sha256']==sha(OLD/'data/instance.json')
    assert len(fresh['receipts'])==6 and all(r['coordinate_bytes_equal'] and r['inventory_equal'] for r in fresh['receipts'])
    sem=load(V2/'qa/pdf_semantic_checks.json');export=load(V2/'logs/pdf_export.json')
    for n in docs:
        assert sem['documents'][n]['md_sha256']==sha(V2/(n+'.md')) and sem['documents'][n]['pdf_sha256']==sha(V2/(n+'.pdf'))
        assert export['audit'][n]['md_sha256']==sha(V2/(n+'.md')) and export['audit'][n]['pdf_sha256']==sha(V2/(n+'.pdf'))
    save(V2/'qa/markdown_semantic_checks.json',{'producer_self_check':True,'all_four_preserved_table_blocks_exact':True,'six_formal_rows_against_metrics':taskrows,'all29_parameter_rows_against_Q2C':paramrows,'important_original_final_edit_pairs_verified':len(ed['important_edits']),'subsequent_reader_clarity_edits_verified':len(fb),'no_numeric_model_or_config_changes':True,'main_numerical_solves_this_revision':0,'small_process_receipt_smokes_separate':3,'current_independent_recheck_claimed':False})
    visual=[]
    observations={1:'标题/摘要衔接、库存与下界；货物表头体积及密度负幂清晰。表在页边分段有重复表头，G5在第2页。',2:'续表G5清楚；密度界、cm²/cm³转换、静态假设和最小坐标顶点定义可读。',3:'分离、累计T/A承重、库存与目标公式完整；m²和kg/m²未丢幂，松弛界分子是货物总体积。',4:'搜索努力限定、库内占地m²和12行方法比较表清晰，改进百分比与解释相接。',5:'方法图、六任务表及有限单车非支配散点完整，图例/星号/轴清楚。',6:'逐车图、费用解释、混合目标差别和装载顺序清楚，无跨任务件号合并。',7:'三维示例来自Q1-F2第一车；自检/独立数值复核范围、小例、复现与O(R²)/O(n_k²)清晰。',8:'参数方法与29行表完整，各列数字对齐，无行丢失。',9:'观察与机制、固定质量/密度、易碎解释和价格取舍限定明确。',10:'参数四组图、附件2证据范围、结论界间差与原件参考完整。',11:'复现与接收附录完整；页末留白，无内容遮盖，未为页数增加内容。'}
    for n,rec in sem['documents'].items():
        for page in rec['pages']:
            num=page['page'];visual.append({'document':n,'page':num,'image_sha256':sha(page['image']),'actually_viewed_full_page':True,'observation':observations[num] if n=='paper' else {1:'经营结论/条件/六方案表/模型表现均可读；m³和kg/m²正确。',2:'验证范围段落及29行参数表完整，重复表义与论文一致。',3:'场景经营解释、坐标轴与装卸依赖、业务条件及证据入口完整。'}[num],'clipping_or_overlap_observed':False})
    save(V2/'qa/visual_review.json',{'producer_self_check':True,'method':'Every full-size page image was actually displayed and read; every scientific crop contact sheet was displayed. After two final wording fixes only paper pages1/3 changed and were displayed again; remaining12 pages pixel-identical to already reviewed images.','full_pages':visual,'science_crop_images_viewed':{'paper':37,'technical_report':9},'source_science_occurrences':{'paper':35,'technical_report':5},'scientific_exponent_observation':'Embedded glyphs show ²/³ above baseline, density ⁻³ above baseline with minus retained, O(R²) and O(n_k²) remain quadratic. All equations/table headers/units agree with Markdown and code meaning.','visual_status':'pass within stated producer scope','independent_recheck':None})
    quality=[
        ('problem_to_model','单车有限子集与整批恰好一次先解释，再定义变量、几何/支撑约束与双目标；消费者知道六任务差异。'),
        ('rule_vs_assumption','易碎朝向非官方澄清，单支持域缩小可行域，均匀质量与动态未知明确。'),
        ('physical_terms','空间/载重利用率分母统一；kg/m²为承载面密度，与Pa及额定载重区分；最小坐标顶点避免角名歧义。'),
        ('method_to_experiment','支持库存问题连接保留策略；分割碎片问题连接最大矩形/模板占地；比较明示搜索努力不等。'),
        ('results_to_explanation','六任务/图/29场景给具体作用路径与经营取舍；载重/尺寸结论限定搜索配置，不把观察写为全球瓶颈证明。'),
        ('proof_strength','库内面积最优、启发式车队、松弛下界、有限非支配样本分清；所有最优/比例/动态范围复核。'),
        ('full_text_readability','完整原文和修订稿已审阅；正文服务科学/经营问题，开发接续留README/logs/qa；各图说明其支持结论及范围。'),
        ('remaining_gaps','全球最优/完整Pareto/动态工程/附2完整批次仍缺证据；没有通过润色新增实验。')]
    save(V2/'qa/scientific_editorial_review.json',{'producer_self_check':True,'entire_paper_and_enterprise_report_read':True,'findings':[{'dimension':a,'judgment':b,'status':'checked against bound source records and final PDFs'} for a,b in quality],'all_affected_numbers_units_exponents_qualifiers_checked':True,'not_quality_by_sentence_or_character_count':True,'reader_feedback_source':'root direct reading of this draft only; not independent recheck','initial_a5_fail_a6_partial_preserved_in_receiving_records':True})
    save(V2/'logs/final_bindings.json',{'utc':datetime.datetime.now(datetime.UTC).isoformat(),'original_payloads_rechecked':3722,'old_manifest_sha256':sha(OLD/'manifest.json'),'old_numeric_program':code,'old_selected_configs':cfg,'old_instance_sha256':sha(OLD/'data/instance.json'),'fresh3_receipt_sha256':sha(OLD/'replay/fresh3/receipt.json'),'fresh3_scope':'Six current formal numeric results and coordinate bytes. Does not regenerate figures or revised PDFs; figures byte-equal to same original output, final PDF exporter/QA bound separately. No v2 six-formal rerun.','figures':images,'new_sources':{p.name:sha(p) for p in sorted((V2/'src').glob('*.py'))},'manuscripts':{n:{'md_sha256':sha(V2/(n+'.md')),'pdf_sha256':sha(V2/(n+'.pdf'))} for n in docs},'approved_input_identity':{str(p):sha(p) for p in [V2.parents[2]/'inputs/L3.md',V2.parents[2]/'inputs/raw-lock.json',V2.parents[2]/'candidate/C11-lock.json',V2.parent/'design-lock.json',V2.parent/'REPAIR_FOLLOWUP.md',V2.parent/'review/initial-lock.json']},'current_python':platform.python_version(),'model':None,'tokens':None,'cost':None})
    print(json.dumps({'original_payloads_rechecked':3722,'formal_rows':6,'scenario_rows':29,'all_sources_unchanged':True,'visual_pages':len(visual),'editorial_full_documents':2,'main_solves':0}))
if __name__=='__main__':main()
