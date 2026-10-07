# R16-02 continuation checkpoint

Task `R16-02` remains with actor `/root/r16_original_solution`; the current directory is the only write domain for this prospective slice. C10 applies prospectively under `runs/R18/amendment.json`. The former C9 attempt is preserved as blocked/unpassed at 2/2. This policy-amendment queue restart is the prospective counter increment to 3, but is not an additional observed source error and does not alter the old verdict. C9 author-history 2/2 remains separate.

The first slice completed within the declared 12-minute local window. Its baseline command ran the actual corrected Attachment 1 DOCX and emitted per-item coordinates for all 3,000 pieces under two all-one-type fleet candidates. The producer's separately implemented checker reopened the raw DOCX and placements, recomputed the quantities, and found zero count, pose, boundary, clearance, payload, or overlap defects. This remains a producer self-check; no independent reviewer has seen the outputs.

Observed floor-only candidates: type 1 uses 75 trips at ¥33,750 total, mean space utilization 19.7451%, mean payload utilization 9.1333%; type 2 uses 40 trips at ¥28,000, 17.2479%, and 10.2750%. Total raw cargo is 41,100 kg and 287,350,000 cm³. The shelf method is feasible under its conservative assumptions but not optimal. Its low rates show a material cost of forbidding stacking; the next justified experiment is a stacking-enabled candidate with explicit support/load/fragile/directional checks and the same raw quantities.

## Requirement state at this checkpoint

| Requirement | Current evidence | State / limit |
|---|---|---|
| Q1: one-truck simultaneous space/load maximization for each type | None yet | Open; objective trade-off needs an explicit Pareto or scalarization policy grounded in the ambiguous word “simultaneously” |
| Q1: one-type fleet to ship all goods, placements and rates | `placements.csv`, `results.json`, `independent-check.json` | Feasible conservative candidates, all floor-only; minimum-trip optimality unproved |
| Q2: mixed-fleet minimum vehicles and minimum cost | None | Open; no mixed assignment/packing optimization or optimality proof |
| Q3: technical report, parameter effects and program performance | Runtime receipts and baseline artifacts only | Open; no full sensitivity study or paper |
| Attachment 2 generality | Raw workbook previously extracted in original producer session, not used in this slice | Open; workbook dimensions have no clear shipment quantities and include ranges/missing laboratory values |
| p1–p5 | Partial source-to-baseline/check trace only | Full acceptance pending |
| Independent fresh-context acceptance | None | Pending; do not call producer self-check independent |

## Next executable action

Construct a stacking-enabled feasible baseline from the same official table. Use a support graph or explicit box-to-box support areas; enforce no overlap, fragile goods at floor or directly supported as allowed, G4/G5 upright orientation and center-of-mass projection containment, 500 kg/m² bearing limits, rated gross capacity, and 3 cm top clearance. Compare it with the preserved floor-only candidates on the same instances. Record any inability to honor a constraint as an observed counterexample and keep the corresponding claims unverified. Then proceed to Q1 and Q2 before drafting the complete Chinese paper.

Reproduction commands (run from repository root):

```powershell
py -3.12 -X utf8 runs/R16/prospective-20261007/baseline.py
py -3.12 -X utf8 runs/R16/prospective-20261007/verify_baseline.py
```

The original execution receipts are `receipts/01-baseline.json` and `receipts/02-independent-check.json`. Fresh reruns are not the original invocation and should receive new unique receipts.
