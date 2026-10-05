from pathlib import Path
root=Path(__file__).resolve().parents[4]
for name in ['runs/R08/validation/inputs/complex-request.json', 'runs/R08/candidate/C7/forge-agent-flow/references/recording-protocol.md', 'runs/R08/candidate/C7/forge-agent-flow/SKILL.md']:
    print('SOURCE '+name); print((root/name).read_text(encoding='utf-8'))
