import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--control',type=Path,required=True);a=p.parse_args()
x=json.loads((a.baseline/'results.json').read_text(encoding='utf-8'))['origins']
y=json.loads((a.control/'results.json').read_text(encoding='utf-8'))['origins']
def vectors(origins): return [[(v['target_date'],v['coordinate_order'],v['residual_units'],v['vector_available_at']) for v in o['calibration_vectors']] for o in origins]
assert vectors(x)==vectors(y), 'lawful exact retransmission changed calibration vector semantics'
print(json.dumps({'status':'lawful_duplicate_semantics_preserved','baseline_day_counts':[len(o['calibration_vectors']) for o in x],'control_day_counts':[len(o['calibration_vectors']) for o in y],'same_dates_coordinate_order_residuals_and_vector_arrivals':True},ensure_ascii=False,indent=2))
