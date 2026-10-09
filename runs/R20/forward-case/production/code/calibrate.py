#!/usr/bin/env python3
"""Deterministic batch-arrival residual calibration; Python standard library only."""
import argparse
import csv
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import sys


class InputError(ValueError):
    pass


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise InputError(f"invalid timestamp: {value!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(hours=8):
        raise InputError(f"expected Asia/Shanghai UTC+08:00 timestamp: {value!r}")
    return parsed


def quantity(value):
    try:
        number = Decimal(value)
    except (InvalidOperation, TypeError) as exc:
        raise InputError(f"invalid units: {value!r}") from exc
    if not number.is_finite() or number < 0:
        raise InputError(f"actual/predicted units must be finite nonnegative: {value!r}")
    return number


def number(value):
    # String representation preserves decimal arithmetic, including signed residuals.
    return format(value.normalize(), 'f') if value else '0'


def read_csv(path, columns):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != columns:
            raise InputError(f"{path.name}: expected columns {columns}")
        rows = []
        for line, row in enumerate(reader, 2):
            if None in row or any(v is None or v == '' for v in row.values()):
                raise InputError(f"{path.name}:{line}: missing or extra field")
            rows.append((line, row))
        return rows


def load(input_dir):
    raw = input_dir / 'raw'
    series_rows = read_csv(raw / 'series.csv', ['series_id'])
    series = [row['series_id'] for _, row in series_rows]
    if not series or len(series) != len(set(series)):
        raise InputError('series.csv must define nonempty unique coordinates')
    decisions = json.loads((raw / 'decisions.json').read_text(encoding='utf-8'))
    if decisions.get('timezone') != 'Asia/Shanghai':
        raise InputError('decisions timezone must be Asia/Shanghai')
    origins = decisions['origins']
    if not origins or len(origins) != len(set(origins)):
        raise InputError('origins must be nonempty and unique')
    for origin in origins:
        timestamp(origin)
    timestamp(decisions['evaluation_label_cutoff'])
    paths = ['series.csv', 'decisions.json', 'forecasts.csv', 'labels.csv']
    hashes = {f'raw/{name}': digest(raw / name) for name in paths}
    forecasts, labels, audit = [], [], []
    for kind, columns in [('forecasts', ['target_date', 'series_id', 'revision', 'forecast_origin', 'available_at', 'prediction_units']),
                          ('labels', ['target_date', 'series_id', 'revision', 'available_at', 'actual_units'])]:
        observations = {}
        versions = {}
        for line, row in read_csv(raw / f'{kind}.csv', columns):
            try:
                date.fromisoformat(row['target_date'])
                revision = int(row['revision'])
            except ValueError as exc:
                raise InputError(f'{kind}.csv:{line}: invalid target/revision') from exc
            if revision < 1 or row['series_id'] not in series:
                raise InputError(f'{kind}.csv:{line}: invalid revision/coordinate')
            timestamp(row['available_at'])
            value_key = 'prediction_units' if kind == 'forecasts' else 'actual_units'
            quantity(row[value_key])
            if kind == 'forecasts':
                timestamp(row['forecast_origin'])
            identity = (row['target_date'], row['series_id'], row.get('forecast_origin'), revision)
            payload = tuple(row[col] for col in columns)
            if identity in versions and versions[identity] != payload:
                raise InputError(f'{kind}.csv:{line}: conflicting same-version observation {identity}')
            versions[identity] = payload
            if payload in observations:
                observations[payload]['source_lines'].append(line)
                audit.append({'source_file': f'raw/{kind}.csv', 'source_line': line,
                              'reason': 'identical_retransmission', 'canonical_source_line': observations[payload]['source_lines'][0]})
                continue
            obs = dict(row, source_file=f'raw/{kind}.csv', source_lines=[line], source_sha256=hashes[f'raw/{kind}.csv'])
            observations[payload] = obs
            (forecasts if kind == 'forecasts' else labels).append(obs)
    fixed_origins = set(row['forecast_origin'] for row in forecasts)
    if len(fixed_origins) != 1:
        raise InputError('ambiguous fixed forecast origins; supply one explicitly selected forecast set')
    return series, decisions, forecasts, labels, audit, hashes


def select(rows):
    return max(rows, key=lambda r: (timestamp(r['available_at']), int(r['revision']))) if rows else None


def calculate(input_dir):
    series, decisions, forecasts, labels, duplicates, hashes = load(input_dir)
    targets = sorted({row['target_date'] for row in forecasts} | {row['target_date'] for row in labels})
    origins_out = []
    for origin in decisions['origins']:
        cutoff = timestamp(origin)
        coordinates, vectors, days, events = [], [], [], []
        for target in targets:
            day_coordinates = []
            for sid in series:
                frows = [r for r in forecasts if r['target_date'] == target and r['series_id'] == sid]
                lrows = [r for r in labels if r['target_date'] == target and r['series_id'] == sid]
                eligible_f = []
                for row in frows:
                    late = timestamp(row['available_at']) > timestamp(row['forecast_origin'])
                    future = timestamp(row['available_at']) > cutoff or timestamp(row['forecast_origin']) > cutoff
                    if late or future:
                        events.append({'kind': 'forecast', 'target_date': target, 'series_id': sid,
                                       'revision': row['revision'], 'available_at': row['available_at'],
                                       'source_lines': row['source_lines'], 'reason': 'after_fixed_forecast_origin' if late else 'not_known_at_decision'})
                    else:
                        eligible_f.append(row)
                eligible_l = []
                for row in lrows:
                    if timestamp(row['available_at']) <= cutoff:
                        eligible_l.append(row)
                    else:
                        events.append({'kind': 'label', 'target_date': target, 'series_id': sid,
                                       'revision': row['revision'], 'available_at': row['available_at'],
                                       'source_lines': row['source_lines'], 'reason': 'not_known_at_decision'})
                chosen_f, chosen_l = select(eligible_f), select(eligible_l)
                for kind, eligible, chosen in [('forecast', eligible_f, chosen_f), ('label', eligible_l, chosen_l)]:
                    for row in eligible:
                        if row is not chosen:
                            events.append({'kind': kind, 'target_date': target, 'series_id': sid,
                                           'revision': row['revision'], 'available_at': row['available_at'],
                                           'source_lines': row['source_lines'], 'reason': 'superseded_at_this_decision'})
                status = 'available' if chosen_f and chosen_l else 'missing_forecast' if not chosen_f else 'label_not_yet_available'
                residual = number(quantity(chosen_l['actual_units']) - quantity(chosen_f['prediction_units'])) if status == 'available' else None
                item = {'decision_origin': origin, 'target_date': target, 'series_id': sid,
                        'forecast': chosen_f, 'label': chosen_l, 'residual_units': residual, 'status': status,
                        'coordinate_available_at': max(chosen_f['available_at'], chosen_l['available_at']) if status == 'available' else None}
                coordinates.append(item)
                day_coordinates.append(item)
            complete = all(c['status'] == 'available' for c in day_coordinates)
            missing = [c['series_id'] for c in day_coordinates if c['status'] != 'available']
            vector_arrival = max(c['coordinate_available_at'] for c in day_coordinates) if complete else None
            days.append({'decision_origin': origin, 'target_date': target, 'required_coordinates': series,
                         'available_coordinates': [c['series_id'] for c in day_coordinates if c['status'] == 'available'],
                         'missing_coordinates': missing, 'complete': complete, 'calibration_eligible': complete,
                         'vector_available_at': vector_arrival,
                         'reason': 'all_required_coordinates_known' if complete else 'incomplete_day_no_imputation'})
            if complete:
                vectors.append({'target_date': target, 'coordinate_order': series,
                                'residual_units': [c['residual_units'] for c in day_coordinates],
                                'vector_available_at': vector_arrival})
        origins_out.append({'decision_origin': origin, 'complete_day_count': len(vectors),
                            'coordinates': coordinates, 'days': days, 'calibration_vectors': vectors, 'selection_events': events})
    return {'schema': 'arrival-calibration/1', 'label_policy': 'latest_available_at_decision_inclusive',
            'forecast_policy': 'latest_available_by_fixed_forecast_origin', 'units': '件',
            'timezone': decisions['timezone'], 'evaluation_label_cutoff': decisions['evaluation_label_cutoff'],
            'evaluation_label_cutoff_used_for_selection': False,
            'required_coordinate_order': series, 'input_sha256': hashes, 'duplicate_events': duplicates, 'origins': origins_out}


def write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def write_csv(path, fields, rows):
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def render(result):
    lines = ['# 分批到达残差校准结果', '',
             '政策：每个新决策原点使用当时最新已到达的标签版本（含等时刻）；原预测只接受其固定 forecast_origin 截止前到达的版本。标签评价截止仅作附带元数据，不用于提前选取标签。残差 = 实际量 − 原预测量，单位件；坐标顺序为 ' + ', '.join(result['required_coordinate_order']) + '。', '',
             '## 原点及完整日向量', '', '| 决策原点 | 完整日数 | 可用日向量（日期：残差） |', '| --- | --- | --- |']
    for o in result['origins']:
        summary = '；'.join(f"{v['target_date']}：({', '.join(v['residual_units'])})" for v in o['calibration_vectors']) or '无'
        lines.append(f"| {o['decision_origin']} | {o['complete_day_count']} | {summary} |")
    lines += ['', '## 所有坐标与到达时刻', '', '| 决策原点 | 目标日 | 坐标 | 预测版本 / 原截止 / 到达 / 件 | 标签版本 / 到达 / 件 | 残差（件） | 状态 |', '| --- | --- | --- | --- | --- | --- | --- |']
    for o in result['origins']:
        for c in o['coordinates']:
            f, l = c['forecast'], c['label']
            ft = f"v{f['revision']} / {f['forecast_origin']} / {f['available_at']} / {f['prediction_units']}" if f else '缺失'
            lt = f"v{l['revision']} / {l['available_at']} / {l['actual_units']}" if l else '尚不可用'
            lines.append(f"| {o['decision_origin']} | {c['target_date']} | {c['series_id']} | {ft} | {lt} | {c['residual_units'] if c['residual_units'] is not None else '—'} | {c['status']} |")
    lines += ['', '## 完整性', '', '| 决策原点 | 日期 | 已具备坐标 | 缺失坐标 | 纳入校准 | 日向量到达 |', '| --- | --- | --- | --- | --- | --- |']
    for o in result['origins']:
        for day in o['days']:
            lines.append(f"| {o['decision_origin']} | {day['target_date']} | {','.join(day['available_coordinates']) or '无'} | {','.join(day['missing_coordinates']) or '无'} | {'是' if day['complete'] else '否'} | {day['vector_available_at'] or '—'} |")
    lines += ['', '## 短科学说明', '',
              '把日期视作样本、series.csv 的坐标视作同一日向量的分量。对原点 o 和坐标 (d,s)，先固定原预测截止，再在 available_at ≤ o 的标签中选择最新版本，计算 r(d,s;o)=y(d,s;o)−ŷ(d,s)。仅当该日全部必需坐标均可知时，向量才进入校准集合；其到达时刻是全部所选来源到达时刻的最大值。版本修订替换同一坐标，完全重传只保留一个观察及全部来源行。', '',
              '第一个原点恰好到达的标签可以使用；第二个原点会更新已到达的修订。原预测截止之后才到达的预测补写即使在新原点之前已到达，也不能改变原预测。未完整的日期保留逐项审计而不补造、不算作样本。上述计数是特定原点的信息集上的完整日期数，不是跨原点独立新增样本数。', '',
              '这一结果提供校准输入池，未估计校准器、置信区间或预测性能。样本少且标签仍可修订，不能从这些原创合成数据推断真实分布或泛化能力。换成固定成熟评价版本政策会得到不同的可用集合，不能与当前政策混用。机器可读来源、版本、行号和 SHA-256 见 results.json；selection-events.csv 给出所有未选版本的原因。']
    return '\n'.join(lines) + '\n'


def publish(result, output):
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / 'results.json', result)
    fields = ['decision_origin', 'target_date', 'series_id', 'forecast_revision', 'forecast_origin', 'forecast_available_at', 'prediction_units', 'forecast_source_lines', 'label_revision', 'label_available_at', 'actual_units', 'label_source_lines', 'residual_units', 'coordinate_available_at', 'status']
    rows = []
    for origin in result['origins']:
        for c in origin['coordinates']:
            f, l = c['forecast'] or {}, c['label'] or {}
            rows.append(dict(decision_origin=c['decision_origin'], target_date=c['target_date'], series_id=c['series_id'],
                             forecast_revision=f.get('revision', ''), forecast_origin=f.get('forecast_origin', ''),
                             forecast_available_at=f.get('available_at', ''), prediction_units=f.get('prediction_units', ''),
                             forecast_source_lines=';'.join(map(str, f.get('source_lines', []))), label_revision=l.get('revision', ''),
                             label_available_at=l.get('available_at', ''), actual_units=l.get('actual_units', ''),
                             label_source_lines=';'.join(map(str, l.get('source_lines', []))), residual_units=c['residual_units'],
                             coordinate_available_at=c['coordinate_available_at'], status=c['status']))
    write_csv(output / 'coordinates.csv', fields, rows)
    write_csv(output / 'days.csv', ['decision_origin', 'target_date', 'complete', 'calibration_eligible', 'available_coordinates', 'missing_coordinates', 'vector_available_at'],
              [{k: ';'.join(v) if isinstance(v, list) else v for k, v in day.items() if k in ['decision_origin', 'target_date', 'complete', 'calibration_eligible', 'available_coordinates', 'missing_coordinates', 'vector_available_at']} for o in result['origins'] for day in o['days']])
    write_csv(output / 'vectors.csv', ['decision_origin', 'target_date', 'coordinate_order', 'residual_units', 'vector_available_at'],
              [dict(decision_origin=o['decision_origin'], target_date=v['target_date'], coordinate_order=';'.join(v['coordinate_order']), residual_units=';'.join(v['residual_units']), vector_available_at=v['vector_available_at']) for o in result['origins'] for v in o['calibration_vectors']])
    write_csv(output / 'selection-events.csv', ['decision_origin', 'kind', 'target_date', 'series_id', 'revision', 'available_at', 'source_lines', 'reason'],
              [dict(event, decision_origin=o['decision_origin'], source_lines=';'.join(map(str, event['source_lines']))) for o in result['origins'] for event in o['selection_events']])
    (output / '说明.md').write_text(render(result), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = calculate(args.inputs)
        publish(result, args.out)
    except (InputError, KeyError, json.JSONDecodeError, FileExistsError) as exc:
        print(f'REJECTED: {exc}', file=sys.stderr)
        return 2
    print(json.dumps({'status': 'produced', 'output': str(args.out.resolve()),
                      'complete_day_counts': [o['complete_day_count'] for o in result['origins']],
                      'duplicate_retransmissions': len(result['duplicate_events'])}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
