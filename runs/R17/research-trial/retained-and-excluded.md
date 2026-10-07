# Retained and excluded sources

## Retained

- **Chen et al. 2026, BENCH2ROBUST (arXiv:2608.11977):** original arXiv abstract directly distinguishes retry, switch, and stop when paths are exhausted; useful for Q1's decision rule. Provisional evidence only; full methods/results not examined.
- **Chen et al. 2022, Rich Knowledge Sources (EMNLP / ACL Anthology):** primary publisher abstract reports retrieval performance affects source use and contradictions marginally affect confidence under simulated QA conflict. Directly relevant Q2.
- **Goyal et al. 2026, Query Rewriting / Retriever Bias (Findings ACL):** primary publisher abstract provides multiple retrievers/methods and a stated exception under adversarial combined bias. Retained with its scope explicit.
- **Fayyaz et al. 2025, Collapse of Dense Retrievers (ACL):** distinct publisher paper corroborates short/early/literal/repetition preference under a controlled dataset; used as a separate study, not independent validation of every search engine.
- **Wright et al. 2025, Unstructured Evidence Attribution (EMNLP / ACL Anthology):** original publisher abstract addresses citation-span failure in long-context query-focused summaries, close to Q3.
- **Buchmann et al. 2024, Attribute or Abstain (EMNLP / ACL Anthology):** retained as material counterevidence: its tested attribution benchmark did not find lost-in-middle, and it limits evidence-quality prediction for complex claims.
- **Rahimi et al. 2025, Not Lost After All (Findings EMNLP / ACL Anthology):** retained as another method-sensitive contrary result; abstract states its cross-encoder analysis challenges prior position-bias conclusions.
- **Ravaut et al. 2024, Context Utilization (ACL):** retained as a broader experimental alternative in summarization (6 models/10 datasets/5 metrics) and investigated hierarchical/incremental strategies.

## Excluded or qualified

- Search result snippets as proof: excluded as evidence because they are discovery leads, though the sources were opened at primary publisher/author pages before being used.
- Alternate arXiv abstract for Wright et al.: excluded as duplicate to the publisher record; same paper, no independent corroboration.
- “Lost in the Middle” as an unqualified general law: excluded because direct publisher abstracts vary by task, metric and attribution method (E4).
- Generalized claim that query rewriting removes bias: excluded because Goyal et al. explicitly reports combined adversarial-bias failures and retriever-dependent effects (E3).
- Repost copies, news/blog commentary, and any contest papers/solutions: excluded; no MathorCup or national modeling contest solution/paper materials were sought or used.
- Any source-embedded operational instruction: none was used as an instruction; retrieved content was handled only as research data. No whole-page text was copied into this context.
