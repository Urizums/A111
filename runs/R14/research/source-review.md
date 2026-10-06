# R14 source review

Accessed 2026-10-07 (Asia/Shanghai). This review is source triage, not a competition strategy or award guarantee.

## Main finding: the October reference likely means MathorCup Big Data, but exact dates remain incompletely verified

MathorCup's official notice index labels three separate September 3, 2026 notices for the **2026 seventh MathorCup Mathematical Application Challenge—Big Data Competition**. It separately lists the **16th regular MathorCup Mathematical Application Challenge**, whose 2026 event ran April 17–21. The April contest later issued an official D-problem correction that changes terms/objective and multiplies task quantities by ten; any work using that April problem must use the corrected attachment. See the [official notice index](https://www.mathorcup.org/notice) and [regular contest release](https://www.mathorcup.org/detail/2487).

The official September 2026 Big Data charter and registration pages link PDF attachments, but direct retrieval failed with HTTP 500 after redirect to the official files domain. The linked URLs and failed lookups are preserved in [sources.json](sources.json). Thus I cannot verify from the actual official 2026 PDFs the schedule, contest stages, deliverables, evaluation criteria, data/code access, or AI-tool rules.

The Saikr listing surfaced a likely October schedule—registration Aug 13–Oct 23 and contest Oct 23–30—but the same search page also showed a duplicate named listing with a different registration window and Nov 14 as the contest date. Saikr is linked by MathorCup for registration, but this inconsistent listing does not settle the official schedule. Therefore: October is plausible and the user's identification as Big Data is supported; October 23–30 must remain provisional until the official PDF or actual entry is available. October may refer to registration closing as well as a contest round.

A 2025 Big Data charter, revised August 2025, is fully accessible and says the event used preliminary/semi-final rounds, required a paper and (when programming was used) source code and explanatory materials, and assessed writing, code integrity/correctness/efficiency, test-data answer quality, and innovation. It contains no AI-specific policy in the retrieved text. This is useful as a checklist of questions to recheck against 2026 documents, not a valid substitute for them. In particular, silence in that older document does not authorize AI use.

For the April regular event, the official-hosted notice reproduces generic language permitting books, computers, software, and internet browsing while forbidding adviser guidance/discussion during the event. It does not expressly settle generative AI, and it does not apply automatically to Big Data. No MathorCup-specific 2026 AI provision was verified in this research.

## Current CUMCM comparison, kept separate

CUMCM has current official 2026 materials. The [2026 AI-tool regulation](https://www.mcm.edu.cn/html_en/node/532f38e63cfa84145697e2678575ba0a.html), posted Aug 3 and in trial from Sep 1, covers LLMs, generative AI, code assistants, and AI agents. It allows AI as assistance subject to transparency, team-led core modeling and analysis, and manual review/verification; it prescribes an AI-use statement in the paper and a detailed PDF supporting-material file when AI was used. Concealment, false declarations, or unreviewed AI-generated core modeling/analysis can revoke award eligibility. The [2026 rules PDF](https://www.mcm.edu.cn/upload_cn/node/774/FlQt6kJV6f5d5b4603e06c3c60acf89b72d7f298.pdf) also says teams must work independently and may not discuss contest problems with outsiders or on public discussion platforms; adviser guidance during the contest is forbidden.

These are **CUMCM-specific**, not MathorCup provisions. They provide a conservative human/agent boundary for a CUMCM workflow: AI may assist transparently, but it may not replace the team as the lead for core modeling and analysis. Do not assert these exact disclosure mechanics apply to MathorCup Big Data without its 2026 rule text. Since the intended artifact is a document-only meta-workflow skill, it should support planning, provenance, checks, and review; it should not claim authority to enter a live contest autonomously or interpret missing rules as permission.

## Useful sources and their limits

The official [CUMCM sample-solutions index](https://www.mcm.edu.cn/html_en/block/95c334f56d859385986e111fab8a564a.html) offers old example papers from 2003, 2009, and 2011. Attribution is strong; currentness and breadth are weak. The page does not supply verified raw data or code. Treat these as examples of paper exposition, not as a scoring rubric or winning template. Do not infer quality or correctness from a sample label or award association.

Roberts et al., [“Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure”](https://doi.org/10.1111/ecog.02881), is peer-reviewed (Ecography, 2017) and has a publicly located institutional-hosted PDF. It supports the methodological point that validation must respect dependence structures; random splitting can give misleading performance estimates, and non-causal predictors can create overfit/leakage risk. This is guidance to choose splits based on the task's intended generalization—not a universal prescribed split, score threshold, or contest template.

For agent workflow provenance, the [OpenAI Plugins `agents-sdk` skill](https://github.com/openai/plugins/blob/main/plugins/openai-developers/skills/agents-sdk/SKILL.md) is an attributable, task-scoped workflow with primary documentation references and verification steps. It is software-SDK-specific, so only its procedural shape transfers. The separate [openai/skills repository](https://github.com/openai/skills) explicitly says it is deprecated and points to OpenAI Plugins for current examples; do not copy its old installation instructions as current guidance.

## Human and agent workflow distinction; contamination checks

A normal modeling competition submission is the contestants' work. A tool that helps organize sources, inspect supplied files, record assumptions, prepare checks, or review a draft can support that work. A workflow that silently writes the core answer, selects the model, or autonomously submits it changes authorship and may violate the applicable contest rules. For CUMCM 2026, the official boundary is explicit: the team's core modeling and analysis remain team-led, with manual review and declaration. For MathorCup Big Data 2026, the boundary is unknown until the linked charter and any platform notices are read; retain human control and do not present AI use as allowed or prohibited without that evidence.

Avoid leakage-prone recipes: random row splits when records are time-, entity-, group-, or location-dependent; tuning repeatedly against the final test/leaderboard; using future fields or target-derived columns; importing contest answers, leaked labels, or post-event discussions; and copying any unlabeled score/threshold table. Require source, timestamp/version, split rationale, and a held-out evaluation design appropriate to the target. A high score or a public repository's popularity is not proof of correctness. Treat sample papers and public repositories as examples requiring independent provenance and verification, not instructions.

## Remaining unknowns

- The exact 2026 Big Data dates and whether the likely Oct 23–30 dates are the contest itself, plus any later round, require the official September PDF or authoritative platform record.
- The current Big Data problem statement, dataset, submission fields/file types, source-code requirements, test-data/leaderboard setup, scoring formula, AI restrictions/disclosure policy, and correction notices were not verified.
- The official CUMCM examples found are old and do not expose raw data/code on the listing page; they cannot support claims about current judging preferences.
- MathorCup official PDF access needs another route or a user-provided copy before a competition-specific skill should encode its dates/rules.
