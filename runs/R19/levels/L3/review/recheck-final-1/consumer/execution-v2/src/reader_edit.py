"""Apply informed reader feedback; move development history to receiving records."""
from pathlib import Path
import json,difflib
V2=Path(__file__).resolve().parents[1]
changes=[
('paper','尺寸、易碎需求和朝向解释会显著改变所得车队','部分尺寸、易碎需求和朝向场景改变了所得车队','摘要对应已运行的具体场景，消除显著一词可能暗示统计检验/普遍未来结论的歧义。','../execution/sensitivity/results.json 原29场景'),
('paper','需求有效体积/单车有效体积','货物总体积/单车有效体积','分子是货物实体体积，只有分母扣除顶部间隙；统一松弛界的物理含义。','../execution/src/solver.py bounds; ../execution/data/instance.json'),
('paper','其左下后角为x(i)、y(i)、z(i)。','其各坐标分量最小的顶点为(x(i),y(i),z(i))。','原点右后下、y朝左的定义使原角名有歧义；与区间[x,x+dx]等真实代码统一。','../execution/src/solver.py expand; ../execution/src/checker.py 边界/重叠区间'),
('paper','独立首审已直接从原件重建输入，复算六任务、168候选、348参数及四个库MILP，并以自有检查器核查主要空间和数值结果；其通过范围仍是明确的单支持、均匀质量和静态条件。首审未完整重跑64次扩展装车与1674次历史重装，且发现旧PDF科学上标丢失、原三项CLI日志细节缺失和两次并发目标偏离。本修订修复表达与导出，不追溯补造历史；修订稿的知情复审仍待进行。','除生产者自检外，另一个审查者从原件重建输入，复算六任务、168候选、348参数及四个库整数规划，并以自有检查器核查主要空间和数值结果；验证范围仍是明确的单支持、均匀质量和静态条件。64次扩展装车与1674次历史重装未被完整重复验证，其记录作为未改善研究保留。文档版本、导出检查和历史运行限制由接收入口README及qa/、logs/提供。','论文保留验证方法与覆盖范围，开发轮次/日志缺口移入接收记录；不删历史、不夸验证范围。','../review/initial/report.md/result.json; logs/resources.json'),
('paper','原计算声明3600秒窗口，已耗1929.69895秒；两次峰值2违反单求解进程目标，首轮3个CLI的原PID/stdout不可恢复，保持null。原全部峰值内存也未观测。新文档修复与前瞻日志测试资源另记，不追认原历史符合；具体收据、表达修改与导出核查见本域logs/和qa/。当前修订仅有作者自检，知情复审待另行完成；比赛规则及真实提交合规仍未核实，本研究没有联网、安装、上传或投稿。','正文结论由逐件坐标、库存守恒、静态荷载核算和参数结果支撑，原三维全局最优与动态运输安全保持未验证。组合接收入口README提供程序身份、复现步骤、文档核查和完整运行限制；这些记录用于判断可复现范围，不改变本研究的条件结论。','将论文附录面向科学复现，原资源/null和待验状态保留README/result/logs。','../execution/logs/resource_final.json; ../execution/logs/invocations.json; 当前README/result'),
('technical_report','独立首审从原件重建并复算主要数值，接受明确静态范围内的模型与可行结果，但旧PDF科学记号导出失败、历史日志保留部分不足；本版修复文字和PDF，知情复审尚未完成。道路加速度、摩擦、绑扎及叉车可达性不在已核查范围内。','主要数值另经从原件重建输入、重新求解和坐标复核，支持明确静态范围内的可行性判断。道路加速度、摩擦、绑扎及叉车可达性不在已核查范围内；现场实施前仍需工程确认。文档版本和具体核查范围见接收入口README。','企业报告让验证证据服务实施判断，审查轮次/旧导出错误分配到接收说明。','../review/initial/report.md/result.json; 原静态模型假设'),
('technical_report','本建议建立在单支持嵌套列、均匀质量和静态承重上，原空间最优与动态安全均未证。原首审及原3600秒窗口内已耗1929.69895秒的事实不改变；旧3个CLI原PID/stdout缺失保持null，两次并发目标偏离不追认符合。新域保留逐次收据、科学表达修改和PDF接收检查，独立知情复审待进行。原程序和数值配置未改，本轮不重复无影响的历史求解。','本建议建立在单支持嵌套列、均匀质量和静态承重上，原三维全局最优与动态安全均未证。实施时优先确认包装规则和支持关系；需求或价格变化后重新选方案。接收入口README集中说明数值程序、配置、证据覆盖和版本状态，完整运行限制留在logs/与qa/，便于技术人员复核。','管理结论回到条件与操作；首审及不可补历史限制完整留入口与机器状态。','原模型/主结果/参数实验；logs/resources.json; 当前README/result'),
]
def main():
    edits=json.loads((V2/'logs/editorial_changes.json').read_text(encoding='utf-8'))
    docs={n:(V2/(n+'.md')).read_text(encoding='utf-8') for n in ['paper','technical_report']}
    log=[]
    for name,old,new,why,evidence in changes:
        assert old in docs[name] or new in docs[name],old
        docs[name]=docs[name].replace(old,new)
        for e in edits['important_edits']:
            if e['document']==('report' if name=='technical_report' else name) and e['revised_sentence'] in old:
                e['first_draft_sentence']=e['revised_sentence'];e['revised_sentence']=new;e['reason']+='；'+why
        log.append({'document':name,'original_draft_sentence':old,'final_sentence':new,'reason':why,'evidence':evidence,'numeric_or_model_change':False})
    for name,new in docs.items():
        (V2/(name+'.md')).write_text(new,encoding='utf-8')
        old=(V2.parent/'execution'/(name+'.md')).read_text(encoding='utf-8')
        (V2/'logs'/f'{name}_editorial.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='../execution/'+name+'.md',tofile=name+'.md')),encoding='utf-8')
    (V2/'logs/editorial_changes.json').write_text(json.dumps(edits,ensure_ascii=False,indent=2),encoding='utf-8')
    (V2/'logs/reader_feedback_changes.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
    assert '左下后角' not in docs['paper']
    for name,txt in docs.items():
        assert not any(s in txt for s in ['PID/stdout','知情复审','峰值2','token'])
    print('Reader feedback applied; numerical and scientific validation scope preserved.')
if __name__=='__main__':main()
