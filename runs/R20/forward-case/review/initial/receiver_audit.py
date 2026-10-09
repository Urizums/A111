#!/usr/bin/env python3
"""Independent source-to-output receiver for the frozen calibration case."""
import argparse, csv, hashlib, json
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path


def dt(v):
    x = datetime.fromisoformat(v)
    if x.tzinfo is None or x.utcoffset() != timedelta(hours=8):
        raise AssertionError(f"timestamp lacks Asia/Shanghai offset: {v}")
    return x


def csv_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return [(i, r) for i, r in enumerate(csv.DictReader(f), 2)]


def derive(inputs):
    raw = inputs / 'raw'
    series = [r['series_id'] for _, r in csv_rows(raw/'series.csv')]
    assert series and len(series) == len(set(series)), 'series definition invalid'
    decisions = json.loads((raw/'decisions.json').read_text(encoding='utf-8'))
    assert decisions['timezone'] == 'Asia/Shanghai'
    origins = decisions['origins']
    hashes = {f'raw/{n}': hashlib.sha256((raw/n).read_bytes()).hexdigest()
              for n in ['series.csv','decisions.json','forecasts.csv','labels.csv']}
    tables = {}
    duplicate_events = []
    for kind, fields in [('forecasts',['target_date','series_id','revision','forecast_origin','available_at','prediction_units']),
                         ('labels',['target_date','series_id','revision','available_at','actual_units'])]:
        rows = csv_rows(raw/f'{kind}.csv')
        versions, payloads = {}, {}
        unique=[]
        for line,row in rows:
            date.fromisoformat(row['target_date'])
            assert row['series_id'] in series
            assert int(row['revision']) > 0
            dt(row['available_at'])
            if kind == 'forecasts': dt(row['forecast_origin'])
            key=(row['target_date'],row['series_id'],row.get('forecast_origin'),int(row['revision']))
            payload=tuple(row[c] for c in fields)
            if key in versions and versions[key] != payload:
                raise AssertionError(f'conflicting source version: {key}')
            versions[key]=payload
            if payload in payloads:
                payloads[payload]['source_lines'].append(line)
                duplicate_events.append({'source_file':f'raw/{kind}.csv','source_line':line,
                                         'reason':'identical_retransmission',
                                         'canonical_source_line':payloads[payload]['source_lines'][0]})
                continue
            item={**row,'source_file':f'raw/{kind}.csv','source_lines':[line],
                  'source_sha256':hashes[f'raw/{kind}.csv']}
            payloads[payload]=item
            unique.append(item)
        tables[kind]=unique
    frows,lrows=tables['forecasts'],tables['labels']
    # The frozen case has a single declared original forecast set.
    assert len({r['forecast_origin'] for r in frows}) == 1, 'multiple fixed forecast origins'
    targets=sorted({r['target_date'] for r in frows}|{r['target_date'] for r in lrows})
    out=[]
    for origin in origins:
        cutoff=dt(origin); coordinates=[]; days=[]; vectors=[]; events=[]
        for target in targets:
            day_coords=[]
            for sid in series:
                fs=[r for r in frows if r['target_date']==target and r['series_id']==sid]
                ls=[r for r in lrows if r['target_date']==target and r['series_id']==sid]
                eligf=[]
                for r in fs:
                    fixed=dt(r['available_at'])<=dt(r['forecast_origin']) and dt(r['forecast_origin'])<=cutoff and dt(r['available_at'])<=cutoff
                    if fixed: eligf.append(r)
                    else: events.append({'kind':'forecast','target_date':target,'series_id':sid,'revision':r['revision'],'available_at':r['available_at'],'source_lines':r['source_lines'],'reason':'after_fixed_forecast_origin' if dt(r['available_at'])>dt(r['forecast_origin']) else 'not_known_at_decision'})
                eligl=[]
                for r in ls:
                    if dt(r['available_at'])<=cutoff: eligl.append(r)
                    else: events.append({'kind':'label','target_date':target,'series_id':sid,'revision':r['revision'],'available_at':r['available_at'],'source_lines':r['source_lines'],'reason':'not_known_at_decision'})
                sf=max(eligf,key=lambda r:(dt(r['available_at']),int(r['revision']))) if eligf else None
                sl=max(eligl,key=lambda r:(dt(r['available_at']),int(r['revision']))) if eligl else None
                for kind,eligible,chosen in [('forecast',eligf,sf),('label',eligl,sl)]:
                    for r in eligible:
                        if r is not chosen:
                            events.append({'kind':kind,'target_date':target,'series_id':sid,'revision':r['revision'],'available_at':r['available_at'],'source_lines':r['source_lines'],'reason':'superseded_at_this_decision'})
                status='available' if sf and sl else ('forecast_not_available' if not sf else 'label_not_yet_available')
                residual=str(Decimal(sl['actual_units'])-Decimal(sf['prediction_units'])) if sf and sl else None
                coord_at=max((sf['available_at'],sl['available_at'])) if sf and sl else None
                c={'decision_origin':origin,'target_date':target,'series_id':sid,'forecast':sf,'label':sl,'residual_units':residual,'status':status,'coordinate_available_at':coord_at}
                coordinates.append(c);day_coords.append(c)
            have=[c['series_id'] for c in day_coords if c['status']=='available']
            missing=[sid for sid in series if sid not in have]
            complete=not missing
            vector_at=max(c['coordinate_available_at'] for c in day_coords) if complete else None
            days.append({'decision_origin':origin,'target_date':target,'required_coordinates':series,'available_coordinates':have,'missing_coordinates':missing,'complete':complete,'calibration_eligible':complete,'vector_available_at':vector_at,'reason':'all_required_coordinates_known' if complete else 'incomplete_day_no_imputation'})
            if complete:
                vectors.append({'target_date':target,'coordinate_order':series,'residual_units':[c['residual_units'] for c in day_coords],'vector_available_at':vector_at})
        out.append({'decision_origin':origin,'complete_day_count':len(vectors),'coordinates':coordinates,'days':days,'calibration_vectors':vectors,'selection_events':events})
    return {'schema':'arrival-calibration/1','label_policy':'latest_available_at_decision_inclusive','forecast_policy':'latest_available_by_fixed_forecast_origin','units':'件','timezone':'Asia/Shanghai','evaluation_label_cutoff':decisions['evaluation_label_cutoff'],'evaluation_label_cutoff_used_for_selection':False,'required_coordinate_order':series,'input_sha256':hashes,'duplicate_events':duplicate_events,'origins':out}


def check_one(path, expected, label):
    if path != expected:
        raise AssertionError(f'{label} mismatch: got {path!r}, expected {expected!r}')


def first_diff(expected, actual, path='$'):
    if type(expected) is not type(actual):
        return path, expected, actual
    if isinstance(expected, dict):
        if expected.keys() != actual.keys():
            return path+'.keys', sorted(expected.keys()), sorted(actual.keys())
        for key in expected:
            diff=first_diff(expected[key],actual[key],f'{path}.{key}')
            if diff: return diff
    elif isinstance(expected, list):
        if len(expected) != len(actual): return path+'.length',len(expected),len(actual)
        for i,(e,a) in enumerate(zip(expected,actual)):
            diff=first_diff(e,a,f'{path}[{i}]')
            if diff: return diff
    elif expected != actual:
        return path, expected, actual
    return None


def audit(inputs, outputs):
    expected=derive(inputs)
    actual=json.loads((outputs/'results.json').read_text(encoding='utf-8'))
    for o in actual.get('origins', []):
        cutoff=dt(o['decision_origin'])
        for c in o.get('coordinates', []):
            f,l=c.get('forecast'),c.get('label')
            if f and (dt(f['available_at']) > dt(f['forecast_origin']) or dt(f['forecast_origin']) > cutoff):
                raise AssertionError(f"independent receiver rejected forecast outside fixed/as-of cutoff: {o['decision_origin']} {c['target_date']} {c['series_id']}")
            if l and dt(l['available_at']) > cutoff:
                raise AssertionError(f"independent receiver rejected future label: {o['decision_origin']} {c['target_date']} {c['series_id']} label available {l['available_at']}")
    # Compare all JSON semantics, including every source field, event and lineage.
    if actual != expected:
        for key in expected:
            if actual.get(key) != expected[key]:
                diff=first_diff(expected[key],actual.get(key),f'$.{key}')
                raise AssertionError(f'results.json mismatch at {diff[0]}: expected {diff[1]!r}; actual {diff[2]!r}')
        raise AssertionError('results.json differs from source reconstruction')
    # Confirm the delimited consumer views agree with JSON, in source field/count terms.
    with (outputs/'coordinates.csv').open(encoding='utf-8-sig',newline='') as f: coords=list(csv.DictReader(f))
    with (outputs/'days.csv').open(encoding='utf-8-sig',newline='') as f: day_rows=list(csv.DictReader(f))
    with (outputs/'vectors.csv').open(encoding='utf-8-sig',newline='') as f: vector_rows=list(csv.DictReader(f))
    ncoord=sum(len(o['coordinates']) for o in expected['origins'])
    nday=sum(len(o['days']) for o in expected['origins'])
    nvec=sum(len(o['calibration_vectors']) for o in expected['origins'])
    assert len(coords)==ncoord, f'coordinates.csv row count {len(coords)} != {ncoord}'
    assert len(day_rows)==nday, f'days.csv row count {len(day_rows)} != {nday}'
    assert len(vector_rows)==nvec, f'vectors.csv row count {len(vector_rows)} != {nvec}'
    # Key CSV values checked against the JSON/source reconstruction.
    coord_by={(r['decision_origin'],r['target_date'],r['series_id']):r for r in coords}
    for o in expected['origins']:
        for c in o['coordinates']:
            row=coord_by[(c['decision_origin'],c['target_date'],c['series_id'])]
            f,l=c['forecast'],c['label']
            assert (row['forecast_revision'] or None)==(f['revision'] if f else None)
            assert (row['forecast_origin'] or None)==(f['forecast_origin'] if f else None)
            assert (row['forecast_available_at'] or None)==(f['available_at'] if f else None)
            assert (row['label_revision'] or None)==(l['revision'] if l else None)
            assert (row['label_available_at'] or None)==(l['available_at'] if l else None)
            assert (row['actual_units'] or None)==(l['actual_units'] if l else None)
            assert (row['residual_units'] or None)==c['residual_units']
            assert row['status']==c['status']
    return {'status':'accepted','origin_complete_day_counts':[len(o['calibration_vectors']) for o in expected['origins']], 'coordinate_rows':ncoord,'day_rows':nday,'vector_rows':nvec,'exact_duplicate_events':len(expected['duplicate_events'])}

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--inputs',type=Path,required=True)
    ap.add_argument('--outputs',type=Path,required=True)
    a=ap.parse_args()
    print(json.dumps(audit(a.inputs,a.outputs),ensure_ascii=False,indent=2))


