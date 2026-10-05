from pathlib import Path
root=Path(__file__).resolve().parents[4]
for name in ['runs/R08/validation/inputs/simple-request.json', 'runs/R08/candidate/C7/forge-agent-flow/references/recording-protocol.md', 'runs/R08/candidate/C7/forge-agent-flow/SKILL.md'] + ['runs/R08/validation/inputs/payments.csv']:
    print('SOURCE '+name); print((root/name).read_text(encoding='utf-8'))
