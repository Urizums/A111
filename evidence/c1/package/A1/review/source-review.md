# A1 independent source review

This review checked the actual A1 output against the unchanged forge-package/1 package and supplied meeting notes. Source-byte hashes match the freeze: package 5804faa670d9ba7475234170c7226c047c424adce761893b4aa039937b77c6bc; notes 2a6802a93f60d87cc1c66f9c0eeed402398dbe0e0ef8df000f4ae76c18bdafdf. The packagectl v1 canonical package digest used in results.json is bd95dfb88fbdf32cc659a0629110da26aef591b1c6f1ba1a24a84b7157db4d75.

## Original v1 acceptance

- quotes — pass (machine): Each of the three source_quote values is an exact substring of the supplied notes. The business JSON file SHA-256 is b0e143bc11dbb572a494397db6c261fd6e574fdc0518c82072cf9a902d5ec5d2.
- commitments — pass (human): The first line assigns updating deployment documentation to 赵宁 and says “周五”; that relative date remains literal. The second assigns adding regression cases to 许静 and gives “2026-10-09”. “决定补充日志告警。” is an explicit decision and is included with owner and due set to null. “建议以后考虑更换配色” is a suggestion and is excluded. “本周没有新增外部通知” is a status statement and is excluded.
- The business file stores the standard Flow response envelope with its actions array nested under artifacts. The inner host reply result carries the same array under result.artifacts.actions. The values satisfy the package output contract and both v1 acceptance rows.
- Chinese explanation — pass: 解释.md (SHA-256 2712985481c278ff83360f29fb4548b5f5930b2fe539a35138f473c0cab19bf0) describes the three included items, literal date, null fields and exclusions without contradiction.
- The independent executable review at check_package_output.py (SHA-256 55633c6d6c554a47cfdd74a1055330ab3cb00592f255a5a491afef3643e2b05f) returned pass in source-checker.json (SHA-256 c0af9f8fc1b1c3641d2dadd68a468c7556bca0128af0f1561ef867cd93adeeb8). Original v1 results.json (SHA-256 1f94035152a833d98db5a6474405cbf06559dc39597927c04b6edad231a2b71e) were assessed by packagectl as pass in package-assess.json (SHA-256 c885c8132119616c9cd10497f22c103e183005bb2936e032c6da71ab038cc775).

## Protocol evidence

The incomplete manual reply draft is preserved in artifacts/worker-reply.draft.json. The worker's captured hostdraft.py check-reply in artifacts/captures/check-reply.json (SHA-256 6ff43b1f2044da71b9ac0856278ab463b6a9babccf094ef798321def0c99c078) returned payload_valid; this validates the outer host reply only. The original hostbridge receive succeeded separately. The worker did not invoke a scaffold generator; its captured authoring scripts and final reply are preserved.

The worker reported one uncaptured setup subprocess: an initial mkdir -p artifacts/captures command was combined with a wrapped read. No capture was fabricated after the fact. Later subprocesses were captured. The worker report is retained in native/worker-progress-message.txt and native/worker-final-message.txt.

## Scope

This is a new-input check, not frozen-case coverage. The no-action input branch was not run; frozen-case coverage remains not assessed. No acceptance row was weakened.
