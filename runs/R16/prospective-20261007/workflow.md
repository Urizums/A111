# R16-02 prospective baseline workflow

Task/actor identity remains `R16-02` / `/root/r16_original_solution`. This dated continuation applies the user-authorized C10 policy amendment in `runs/R18/amendment.json`; p1–p5 remain unchanged. The fixed C9 attempt is still blocked and unpassed at 2/2. No old R16 files or receipts are modified here.

## Declared first-slice resource window

Before executing the baseline, I declare a 12-minute local CPU/wall-work window for this first slice, starting with the recorded baseline command and ending when its first full run and receiving check complete or the window expires. This is a local work bound, not a provider-enforced timer. No install, network lookup, or solution search is included. Python is explicitly `py -3.12 -X utf8`. Actual command elapsed time is recorded where available; model/token/cost telemetry remains unknown.

## Decision and check path

| Step | Input / unit | Decision or operation | Output | Receiving check | Failure route |
|---|---|---|---|---|---|
| Source baseline | Corrected Attachment 1 DOCX; cm, kg, counts | Read tables; make a deterministic conservative shelf-packing baseline with every item on the floor, no stacking | One item coordinate/pose per piece for type-1-only and type-2-only fleets | Independent pass checks dimensions, height clearance, payload, exact item counts, and pairwise non-overlap | Preserve counterexample and classify tool recovery vs model defect; do not call it feasible |
| Scope interpretation | Corrected PDF and DOCX | Use coordinate origin at right-rear-bottom; record axis convention. Keep G4/G5 in printed upright orientation. Treat all other rigid boxes as freely permutable. | Explicit baseline assumptions | Compare each assumption with original clauses; stack and 500 kg/m² constraints are avoided by placing all pieces at z=0 | Mark baseline conservative and incomplete if results do not address stacking |
| Continue full task | Corrected PDF/DOCX/XLSX, p1–p5 | After a checked feasible baseline, address Q1 single-truck trade-off and fleet minimum trips; Q2 mixed fleet truck-count and cost objectives; Q3 parameter sensitivity/report and XLSX genericity | Candidate experiments and full paper, later | Requirement-to-input/model/result/check/limit map; fresh-context review still required | Keep all uncomputed subquestions open |

## First-slice assertions

The baseline is only a feasible packing candidate if the receiving check finds zero missing pieces, boundary violations, height/safety-clearance violations, payload violations, or 3D intersections in every reported trip. Each load uses one trip. For all-floor placement, fragile goods have full floor support, there is no load transmitted to lower goods, and all stacked-centroid/stack-strength constraints are vacuous. This does not prove optimality or answer the stacking-enabled original model.

The two all-one-type plans are comparison candidates, not mixed-fleet optima. A passed check supports only feasibility under the conservative floor-only interpretation and the official Attachment 1 numbers. It does not establish Q1's simultaneous fill/load optimum, fewest trips, minimum cost, attachment-2 generality, or paper completeness.
