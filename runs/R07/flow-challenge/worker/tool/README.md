# Local equipment allocation advice

Requires Python 3. No packages or network access. From any shell, run:

```bash
python3 /workspace/scratch/73714494ad2f/forge-takeover-r07/runs/R07/flow-challenge/worker/tool/allocator.py --equipment /workspace/scratch/73714494ad2f/forge-takeover-r07/runs/R07/flow-challenge/worker/inputs/equipment.csv --requests /workspace/scratch/73714494ad2f/forge-takeover-r07/runs/R07/flow-challenge/worker/inputs/requests.csv --rules /workspace/scratch/73714494ad2f/forge-takeover-r07/runs/R07/flow-challenge/worker/inputs/rules.json --out /workspace/scratch/73714494ad2f/forge-takeover-r07/runs/R07/flow-challenge/worker/results/allocation.json
```

The program emits one row per original request, retaining source row and raw fields, ordered allocation IDs, inventory remaining by equipment/date, source-file digests and reason/rule-basis fields. It only writes the specified local output.
