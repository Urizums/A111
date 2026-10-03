# B1 independent source review

This review checked the actual B1 output against the unchanged forge-package/1 package and the supplied meeting notes. The source-byte hashes match the freeze: package 5804faa670d9ba7475234170c7226c047c424adce761893b4aa039937b77c6bc; notes 2a6802a93f60d87cc1c66f9c0eeed402398dbe0e0ef8df000f4ae76c18bdafdf. The packagectl v1 package_hash is its canonical package-object digest, bd95dfb88fbdf32cc659a0629110da26aef591b1c6f1ba1a24a84b7157db4d75; the first assessment attempt mistakenly supplied the source-byte hash and is preserved with its correction record.

## Original v1 acceptance

- quotes — pass (machine): All three source_quote strings are exact substrings of the supplied notes. actions.json SHA-256: ba34b34ba9ad7f78f67262305170ab6805a1b3f0a5466fdb90e8311e021e7030.
- commitments — pass (human): The first line assigns updating deployment documentation to 赵宁 and says “周五”; the output preserves that literal relative date. The second line assigns adding regression cases to 许静 and preserves 2026-10-09. “决定补充日志告警。” is an explicit decision to add alerts, so it is included with owner and due set to null. “建议以后考虑更换配色。” is a suggestion and is excluded. “本周没有新增外部通知。” is a status statement and is excluded.
- Chinese explanation — pass: 解释.md (SHA-256 a62edee87f4ef97a1cc5a61b9c2f8fa849c66ec3c4b2584dbbf8de3d7843aeb7) describes those three included items, the missing fields, the literal relative date, and both exclusions without contradiction.
- The independent executable review at check_package_output.py (SHA-256 b59e0ec69e9155fa5f24ec77ee68207b7665d456727358fbcfdd96736124e727) returned pass in source-checker.json (SHA-256 64d025fba4e0f484797b51374bb3d851fbf901c9b11b30d64226011ae6a5ebcd). Original v1 results are preserved in results.json (SHA-256 947bfd15d8807871ee8720ea5c013bb4927749c024bf1622e7d09059a68dc497); packagectl assess returned pass in package-assess-corrected.json (SHA-256 653539790866841bd0350224d4f175603ab08b97d52ca571dc08fa12b7201eb6).

## Protocol evidence and retained corrections

The final worker reply (SHA-256 9f2c7cfd387396735b1f033f6efb423a730a96f1dac425a0865c98a778e7b4bf) carried the current invocation and the same business actions. The worker's captured hostdraft.py check-reply returned payload_valid (capture SHA-256 602f571b02ab6f6be7f12f63e68adc608b862245418b8029e8ddb7328e79534b); this validates the outer host reply only. The original hostbridge receive succeeded separately.

The worker preserved an initial malformed actions.json as actions.rejected.json: it ended with literal backslash-n bytes, and the captured verifier failed with JSONDecodeError: Extra data. It then corrected the output; the final actions.json passes the independent check. The preserved worker-reply.preflight-rejected.json also ended with literal backslash-n bytes. No failed hostdraft.py check-reply invocation for that earlier version appears in the worker captures; the final captured check-reply passes. These are two worker correction attempts; both original versions and captures remain present.

My first packagectl assess attempt failed because I used the raw source-byte hash where v1 requires the canonical package-object digest. That failed call is retained in logs/023-write-v1-results.json / review/package-assess.json, with the first results file copied to results.rejected.json; the corrected canonical digest produced the passing assessment above.

## Scope

This is a new-input check of the supplied notes, not frozen-case coverage. The no-action input branch was not run, and frozen-case coverage remains not assessed. No acceptance row was weakened.
