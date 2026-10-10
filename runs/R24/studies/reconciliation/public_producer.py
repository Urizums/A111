#!/usr/bin/env python3
"""Author-side data producer for a public reconciliation case.

Does not import or read the research grader, oracle, or model tools.
Do not confuse this with an independent Agent or human consumer.
"""
from __future__ import annotations
import argparse
import csv
import json
import re
import sys
from pathlib import Path

INVOICE = ('invoice_id','vendor','total_cents','paid_cents','outstanding_cents')
VENDOR = ('vendor','outstanding_cents')


def execute(producer: Path, destination: Path) -> dict:
    # The authorized runner must additionally compare the public file hashes
    # against its frozen source bundle immediately before and after this call.
    producer = producer.resolve(strict=True)
    if destination.exists():
        raise FileExistsError('Refusing to overwrite a prior submission')
    brief = (producer/'brief.md').read_text(encoding='utf-8')
    match = re.search(r'\bas of (\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ)', brief)
    if match is None:
        raise ValueError('No as-of timestamp in public business brief')
    cutoff = match.group(1)
    invoices = json.loads((producer/'invoices.json').read_text(encoding='utf-8'))
    amendments = json.loads((producer/'amendments.json').read_text(encoding='utf-8'))
    payments = json.loads((producer/'payments.json').read_text(encoding='utf-8'))
    ledger, vendor_balances = [], {}
    for invoice in invoices:
        reference = invoice['invoice_id']
        revisions = [a for a in amendments
                     if a['invoice_id'] == reference and a['state'] == 'approved'
                     and a['approved_at'] <= cutoff]
        revisions.sort(key=lambda a: (a['approved_at'], a['change_id']))
        amount = revisions[-1]['revised_total_cents'] if revisions else invoice['total_cents']
        paid = sum(p['cents'] for p in payments
                   if p['invoice_id'] == reference and p['state'] == 'posted'
                   and p['posted_at'] <= cutoff)
        outstanding = amount - paid
        ledger.append({'invoice_id': reference, 'vendor': invoice['vendor'],
                       'total_cents': amount, 'paid_cents': paid,
                       'outstanding_cents': outstanding})
        vendor_balances[invoice['vendor']] = vendor_balances.get(invoice['vendor'], 0) + outstanding
    summary = [{'vendor': vendor, 'outstanding_cents': cents}
               for vendor, cents in vendor_balances.items()]
    destination.mkdir(parents=True)
    for filename, headings, rows in [('ledger.csv', INVOICE, ledger),
                                      ('suppliers.csv', VENDOR, summary)]:
        with (destination/filename).open('w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=headings)
            writer.writeheader()
            writer.writerows(rows)
    (destination/'workflow.md').write_text(
        'Start from the dated business brief and the downstream field contract. '
        'Read each invoice and use its latest approved amendment available by the stated '
        'cutoff (including equal timestamps), replacing—not stacking—its total. '
        'Sum only posted payments available by that cutoff, excluding void and later events. '
        'Calculate the signed balance in integer cents for every invoice. '
        'Group all invoices by supplier even when their aggregate is zero. '
        'Write both CSV files with the exact downstream columns; recompute vendor totals '
        'from the invoice balances and compare source identities before sending them onward. '
        'If source versions change or a rule cannot be resolved, stop delivery and request a new frozen input.\n',
        encoding='utf-8')
    return {'invoice_rows': len(ledger), 'vendor_rows': len(summary),
            'cutoff': cutoff, 'data_source': 'public inputs only',
            'model_execution': False, 'independent_consumer': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--producer', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    try:
        result = execute(args.producer, args.out)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({'error': str(exc)},ensure_ascii=False),file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
