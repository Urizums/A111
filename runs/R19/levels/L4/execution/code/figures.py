from pathlib import Path
import json,csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

E=Path(__file__).resolve().parents[1];font_manager.fontManager.addfont('C:/Windows/Fonts/simsun.ttc');plt.rcParams.update({'font.family':'SimSun','axes.unicode_minus':False,'font.size':10});F=E/'figures';F.mkdir(exist_ok=True);provenance={}
colors={'G1':'#4195bf','G2':'#83bd58','G3':'#efac43','G4':'#be7dae','G5':'#b96b69'}
def save(fig,name,source):
    fig.savefig(F/(name+'.png'),dpi=180,bbox_inches='tight');plt.close(fig);provenance[name+'.png']=source

def main():
    selection=json.loads((E/'results/selected.json').read_text(encoding='utf8'));single=E/selection['single_root'];pareto=json.loads((single/'pareto.json').read_text(encoding='utf8'))
    fig,axs=plt.subplots(1,2,figsize=(10,3.7))
    for ax,(vt,pts) in zip(axs,pareto.items()):
        ax.scatter([100*p['UV'] for p in pts],[100*p['UW'] for p in pts],color='#227ca6');ax.plot([100*p['UV'] for p in pts],[100*p['UW'] for p in pts],alpha=.5)
        ax.set(xlabel='满容率 UV (%)',ylabel='满载率 UW (%)',title=vt+' 有限非支配档案');ax.grid(alpha=.25)
    save(fig,'pareto',str(single.relative_to(E)/'pareto.json'))
    modes=['baseline_refined','classic_refined','improved_refined'];fig,axs=plt.subplots(1,2,figsize=(10,3.7));records=[]
    for mode in modes:
        s=json.loads((E/'results'/mode/'run_summary.json').read_text(encoding='utf8'));records.append(s)
    x=np.arange(4);labels=['T1整批','T2整批','混型最少车','混型最低费']
    for i,(mode,ss) in enumerate(zip(modes,records)):
        axs[0].bar(x+(i-1)*.23,[s['truck_count'] for s in ss['scenarios']],width=.23,label=mode.split('_')[0]);axs[1].bar(x+(i-1)*.23,[s['cost'] for s in ss['scenarios']],width=.23,label=mode.split('_')[0])
    for ax in axs:ax.set_xticks(x,labels);ax.legend(fontsize=8);ax.grid(axis='y',alpha=.2)
    axs[0].set_ylabel('车辆数');axs[1].set_ylabel('运输费用 (元/趟批次)');save(fig,'method_comparison',[f'results/{m}/run_summary.json' for m in modes])
    for scenario in ['Q1_fleet_T1','Q1_fleet_T2','Q2_min_cost']:
        root=E/selection['scenarios'][scenario]['root'];rows=list(csv.DictReader((root/'placements.csv').open(encoding='utf-8-sig')));truck=rows[0]['truck_id'];rs=[r for r in rows if r['truck_id']==truck];v=json.loads((E/'data/instance.json').read_text(encoding='utf8'))['vehicles'][0 if rs[0]['vehicle_type']=='T1' else 1];L,W,H=v['dims']
        fig=plt.figure(figsize=(10,5));ax=fig.add_subplot(121,projection='3d');side=fig.add_subplot(222);top=fig.add_subplot(224)
        for r in rs:
            x,y,z,l,w,h=[float(r[k]) for k in ['x','y','z','l','w','h']];c=colors[r['cargo_type']]
            vv=np.array([[x,y,z],[x+l,y,z],[x+l,y+w,z],[x,y+w,z],[x,y,z+h],[x+l,y,z+h],[x+l,y+w,z+h],[x,y+w,z+h]])
            faces=[[vv[i] for i in face] for face in [[0,1,2,3],[4,5,6,7],[0,1,5,4],[2,3,7,6],[1,2,6,5],[0,3,7,4]]]
            ax.add_collection3d(Poly3DCollection(faces,facecolors=c,edgecolors='white',linewidths=.15,alpha=.55))
            side.add_patch(Rectangle((x,z),l,h,facecolor=c,edgecolor='white',lw=.25,alpha=.35));top.add_patch(Rectangle((x,y),l,w,facecolor=c,edgecolor='white',lw=.25,alpha=.35))
        ax.set(xlim=(0,L),ylim=(0,W),zlim=(0,H),xlabel='x 向前/cm',ylabel='y 向左/cm',zlabel='z 向上/cm');ax.set_box_aspect((L,W,H));ax.view_init(25,-65);ax.text(0,0,0,'O 右后下',fontsize=8)
        side.set(xlim=(0,L),ylim=(0,H),xlabel='x/cm',ylabel='z/cm',title='侧视投影（不同y可覆盖）');top.set(xlim=(0,L),ylim=(0,W),xlabel='x/cm',ylabel='y/cm',title='俯视投影（不同z可覆盖）')
        fig.suptitle(scenario+' '+truck+' 代表车辆；完整件号/姿态见坐标CSV');fig.legend(handles=[Rectangle((0,0),1,1,color=c,label=g) for g,c in colors.items()],loc='lower center',ncol=5);fig.tight_layout(rect=(0,.06,1,.94));save(fig,'layout_'+scenario,str(root.relative_to(E)/'placements.csv'))
    param=list(csv.DictReader((E/'results/parameter_results.csv').open(encoding='utf-8-sig')));b=next(r for r in param if r['scenario']=='base')
    fig,axs=plt.subplots(2,2,figsize=(10,7))
    for ax,(prefix,labels,vals) in zip(axs.ravel(),[('payload_', ['0.5','1','1.5'],['payload_0.5','base','payload_1.5']),('gap_',['3','10','30'],['base','gap_10','gap_30']),('pressure_',['250','500','750'],['pressure_250','base','pressure_750']),('dimensions_',['0.95','1','1.05'],['dimensions_0.95','base','dimensions_1.05'])]):
        rr=[next(r for r in param if r['scenario']==s) for s in vals];ax.plot(labels,[float(r['cost']) for r in rr],marker='o',color='#21799e');ax.set(title={'payload_':'载重倍数','gap_':'安全间隙/cm','pressure_':'承重阈值/(kg/m²)','dimensions_':'货物尺寸倍数'}[prefix],ylabel='费用/元');ax.grid(alpha=.25)
    fig.suptitle('合成参数改变后重新优化（相同8秒主问题窗口）');fig.tight_layout();save(fig,'parameters','results/parameter_results.csv')
    fig,axs=plt.subplots(1,2,figsize=(10,3.7));scales=[next(r for r in param if r['scenario']==s) for s in ['scale_0.25','scale_0.5','base','scale_2']]
    axs[0].plot([int(r['inventory_items']) for r in scales],[float(r['elapsed_seconds']) for r in scales],marker='o');axs[0].set(xlabel='合成库存件数',ylabel='总计算时间/s',title='规模测试：相同模式/求解时间窗口');axs[1].bar([r['method'] for r in records],[r['elapsed_seconds'] for r in records]);axs[1].set(ylabel='完整官方场景计算时间/s',title='路线实际计算成本');save(fig,'performance',['results/parameter_results.csv']+[f'results/{m}/run_summary.json' for m in modes])
    (E/'checks/figure_provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':main()
