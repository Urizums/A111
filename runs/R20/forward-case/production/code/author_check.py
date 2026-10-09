"""Separate source recomputation and published consumer-interface checks (same author)."""
import argparse
import csv
from datetime import datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys


def csv_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def source_rows(path, relative):
    grouped = {}
    for index, row in enumerate(csv_rows(path), 2):
        key = tuple(row.items())
        if key in grouped:
            grouped[key]['source_lines'].append(index)
        else:
            grouped[key] = dict(row, source_file=relative, source_lines=[index],
                                source_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    return list(grouped.values())


def decstr(value):
    return format(value.normalize(), 'f') if value else '0'


def check(input_dir, output_dir):
    raw = input_dir / 'raw'
    forecasts = source_rows(raw / 'forecasts.csv', 'raw/forecasts.csv')
    labels = source_rows(raw / 'labels.csv', 'raw/labels.csv')
    series = [r['series_id'] for r in csv_rows(raw / 'series.csv')]
    decisions = json.loads((raw / 'decisions.json').read_text(encoding='utf-8'))
    result = json.loads((output_dir / 'results.json').read_text(encoding='utf-8'))
    assert result['label_policy'] == 'latest_available_at_decision_inclusive'
    assert result['forecast_policy'] == 'latest_available_by_fixed_forecast_origin'
    assert result['timezone'] == decisions['timezone'] == 'Asia/Shanghai'
    assert result['units'] == '件'
    assert result['required_coordinate_order'] == series
    assert result['evaluation_label_cutoff'] == decisions['evaluation_label_cutoff']
    assert result['evaluation_label_cutoff_used_for_selection'] is False
    for path in ['forecasts.csv', 'labels.csv', 'series.csv', 'decisions.json']:
        assert result['input_sha256']['raw/' + path] == hashlib.sha256((raw / path).read_bytes()).hexdigest()
    expected_duplicates = []
    for relative, rows in [('raw/forecasts.csv', forecasts), ('raw/labels.csv', labels)]:
        for row in rows:
            for line in row['source_lines'][1:]:
                expected_duplicates.append({'source_file': relative, 'source_line': line,
                                            'reason': 'identical_retransmission', 'canonical_source_line': row['source_lines'][0]})
    assert result['duplicate_events'] == expected_duplicates, 'dedup provenance mismatch'
    assert [o['decision_origin'] for o in result['origins']] == decisions['origins']
    targets = sorted({r['target_date'] for r in forecasts + labels})
    checked_coordinates, checked_days, checked_events, equal_boundary = 0, 0, 0, 0
    coord_csv, days_csv, vector_csv, events_csv = [csv_rows(output_dir / name) for name in ['coordinates.csv', 'days.csv', 'vectors.csv', 'selection-events.csv']]
    expected_coord_csv, expected_day_csv, expected_vector_csv, expected_event_csv = [], [], [], []
    expected_note_rows = []
    for published in result['origins']:
        origin = published['decision_origin']
        dt = datetime.fromisoformat(origin)
        assert len(published['coordinates']) == len(targets) * len(series)
        assert len(published['days']) == len(targets)
        coords_by_key = {(c['target_date'], c['series_id']): c for c in published['coordinates']}
        assert len(coords_by_key) == len(published['coordinates']), 'duplicate coordinate'
        wanted_vectors = []
        wanted_events = []
        for target in targets:
            residuals, arrivals, available, missing = [], [], [], []
            for sid in series:
                foptions = [r for r in forecasts if r['target_date'] == target and r['series_id'] == sid]
                loptions = [r for r in labels if r['target_date'] == target and r['series_id'] == sid]
                allowed_f = [r for r in foptions if datetime.fromisoformat(r['available_at']) <= datetime.fromisoformat(r['forecast_origin']) <= dt]
                allowed_l = [r for r in loptions if datetime.fromisoformat(r['available_at']) <= dt]
                def latest(options):
                    # Reverse sorting rather than invoking the producer's selection helper.
                    return sorted(options, key=lambda r: (datetime.fromisoformat(r['available_at']), int(r['revision'])), reverse=True)[0] if options else None
                f, l = latest(allowed_f), latest(allowed_l)
                c = coords_by_key[(target, sid)]
                assert c['decision_origin'] == origin
                assert c['forecast'] == f, f'wrong fixed forecast {origin}/{target}/{sid}'
                assert c['label'] == l, f'wrong decision-time label {origin}/{target}/{sid}'
                expected_status = 'available' if f and l else 'missing_forecast' if not f else 'label_not_yet_available'
                expected_residual = decstr(Decimal(l['actual_units']) - Decimal(f['prediction_units'])) if f and l else None
                expected_arrival = max(f['available_at'], l['available_at']) if f and l else None
                assert c['status'] == expected_status
                assert c['residual_units'] == expected_residual, 'arithmetic mismatch'
                assert c['coordinate_available_at'] == expected_arrival
                checked_coordinates += 1
                if f and l:
                    assert datetime.fromisoformat(expected_arrival) <= dt
                    available.append(sid)
                    residuals.append(expected_residual)
                    arrivals.append(expected_arrival)
                    equal_boundary += int(l['available_at'] == origin)
                else:
                    missing.append(sid)
                ff, ll = f or {}, l or {}
                expected_coord_csv.append(dict(decision_origin=origin, target_date=target, series_id=sid,
                    forecast_revision=ff.get('revision', ''), forecast_origin=ff.get('forecast_origin', ''),
                    forecast_available_at=ff.get('available_at', ''), prediction_units=ff.get('prediction_units', ''),
                    forecast_source_lines=';'.join(map(str, ff.get('source_lines', []))), label_revision=ll.get('revision', ''),
                    label_available_at=ll.get('available_at', ''), actual_units=ll.get('actual_units', ''),
                    label_source_lines=';'.join(map(str, ll.get('source_lines', []))), residual_units=expected_residual or ('0' if expected_residual == '0' else ''),
                    coordinate_available_at=expected_arrival or '', status=expected_status))
                ft = f"v{f['revision']} / {f['forecast_origin']} / {f['available_at']} / {f['prediction_units']}" if f else '缺失'
                lt = f"v{l['revision']} / {l['available_at']} / {l['actual_units']}" if l else '尚不可用'
                expected_note_rows.append(f"| {origin} | {target} | {sid} | {ft} | {lt} | {expected_residual if expected_residual is not None else '—'} | {expected_status} |")
                for kind, options, chosen in [('forecast', foptions, f), ('label', loptions, l)]:
                    for r in options:
                        if kind == 'forecast' and datetime.fromisoformat(r['available_at']) > datetime.fromisoformat(r['forecast_origin']):
                            reason = 'after_fixed_forecast_origin'
                        elif datetime.fromisoformat(r['available_at']) > dt or (kind == 'forecast' and datetime.fromisoformat(r['forecast_origin']) > dt):
                            reason = 'not_known_at_decision'
                        elif r != chosen:
                            reason = 'superseded_at_this_decision'
                        else:
                            continue
                        wanted_events.append(dict(kind=kind, target_date=target, series_id=sid, revision=r['revision'], available_at=r['available_at'], source_lines=r['source_lines'], reason=reason))
            complete = not missing
            vector_arrival = max(arrivals) if complete else None
            expected_day = dict(decision_origin=origin, target_date=target, required_coordinates=series,
                                available_coordinates=available, missing_coordinates=missing, complete=complete,
                                calibration_eligible=complete, vector_available_at=vector_arrival,
                                reason='all_required_coordinates_known' if complete else 'incomplete_day_no_imputation')
            assert next(d for d in published['days'] if d['target_date'] == target) == expected_day
            checked_days += 1
            expected_day_csv.append(dict(decision_origin=origin, target_date=target, complete=str(complete), calibration_eligible=str(complete), available_coordinates=';'.join(available), missing_coordinates=';'.join(missing), vector_available_at=vector_arrival or ''))
            expected_note_rows.append(f"| {origin} | {target} | {','.join(available) or '无'} | {','.join(missing) or '无'} | {'是' if complete else '否'} | {vector_arrival or '—'} |")
            if complete:
                wanted_vectors.append(dict(target_date=target, coordinate_order=series, residual_units=residuals, vector_available_at=vector_arrival))
                expected_vector_csv.append(dict(decision_origin=origin, target_date=target, coordinate_order=';'.join(series), residual_units=';'.join(residuals), vector_available_at=vector_arrival))
        assert published['calibration_vectors'] == wanted_vectors, 'complete vector inclusion mismatch'
        assert published['complete_day_count'] == len(wanted_vectors)
        # Event ordering is presentation, not a scientific invariant.
        encoded = lambda e: json.dumps(e, sort_keys=True)
        assert sorted(map(encoded, published['selection_events'])) == sorted(map(encoded, wanted_events)), 'selection audit mismatch'
        checked_events += len(wanted_events)
        expected_event_csv += [dict(event, decision_origin=origin, source_lines=';'.join(map(str, event['source_lines']))) for event in wanted_events]
        summary = '；'.join(f"{v['target_date']}：({', '.join(v['residual_units'])})" for v in wanted_vectors) or '无'
        expected_note_rows.append(f"| {origin} | {len(wanted_vectors)} | {summary} |")
    assert coord_csv == expected_coord_csv, 'coordinate CSV differs from source recomputation'
    assert days_csv == expected_day_csv, 'day CSV differs from source recomputation'
    assert vector_csv == expected_vector_csv, 'vector CSV differs from source recomputation'
    canonical = lambda row: json.dumps(row, ensure_ascii=False, sort_keys=True)
    assert sorted(map(canonical, events_csv)) == sorted(map(canonical, expected_event_csv)), 'event CSV mismatch'
    note = (output_dir / '说明.md').read_text(encoding='utf-8')
    for line in expected_note_rows:
        assert line in note, f'missing/incorrect scientific consumer row: {line}'
    assert '未估计校准器、置信区间或预测性能' in note
    assert equal_boundary > 0, 'this supplied-case smoke must exercise equal-time availability'
    return {'status': 'author_checks_pass', 'independent': False, 'checked_coordinates': checked_coordinates,
            'checked_days': checked_days, 'checked_selection_events': checked_events, 'boundary_labels': equal_boundary,
            'checked_note_rows': len(expected_note_rows), 'complete_day_counts': [o['complete_day_count'] for o in result['origins']],
            'requirements': ['fixed forecast arrival', 'latest inclusive label', 'per-origin provenance', 'residual arithmetic',
                             'complete vectors only', 'no imputation', 'dedup', 'all CSV and Chinese tables'],
            'limit': 'Same author, separate recomputation; not independent acceptance or generality/performance evidence.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--outputs', type=Path, required=True)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    try:
        report = check(args.inputs, args.outputs)
    except (AssertionError, KeyError, ValueError) as exc:
        print(f'REJECTED by receiving check: {exc}', file=sys.stderr)
        return 2
    if args.report:
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
