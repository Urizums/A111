# Evidence cards — R17 C10 research trial

Source claims below were checked in the original publisher/author pages at the linked abstract passages; quotes are short location anchors. They are evidence about defined study conditions, not universal agent policy.

## E1 — Recovery choice depends on failure/path state

- **Source:** Chen et al., “Retry, Switch, or Abstain? Learning Strategy-Aware Tool-Use Policies via Controlled Error Injection,” arXiv:2608.11977, v1 submitted 2026-08-12. [arXiv record](https://arxiv.org/abs/2608.11977), abstract lines 16–19.
- **Checked:** It defines episodes in which retry, switching, or stopping after available paths are exhausted are distinct actions. Study covers seven models, four families, two multi-turn benchmark families; abstract reports a robustness gap under injected tool failures, with reported held-out Retail gains for interventions.
- **Supports / decision:** A next action should depend on diagnosed transient/persistent/silent failure and whether a viable alternative remains; justify further work by a changed recovery hypothesis or route. A local ineffective route can stop while independent task work continues.
- **Does not establish:** Best stopping rule for arbitrary web research, broad business tasks, performance outside study settings, cost/time savings, or any universal error count. Only the abstract was inspected in this pass.

## E2 — Retrieval selection and conflict can distort answers

- **Source:** Chen, Zhang & Choi, “Rich Knowledge Sources Bring Complex Knowledge Conflicts,” EMNLP 2022. [ACL Anthology record](https://aclanthology.org/2022.emnlp-main.146/), abstract lines 57–60.
- **Checked:** The authors simulated conflicts between parametric knowledge and retrieved passages; report that retrieval performance affects which sources are used and contradictions only marginally affect model confidence in their tested setting.
- **Supports / decision:** Compare premises and evidence at source level; keep materially conflicting evidence visible and report abstention/uncertainty rather than allowing fluency or confidence alone to decide.
- **Does not establish:** That every model or topic responds this way, or a general best conflict-resolution algorithm. The abstract describes simulated QA conflicts, not open-ended research-agent behavior.

## E3 — Query/retriever bias is not fixed by a generic rewrite

- **Source:** Goyal et al., “Masking or Mitigating? Deconstructing the Impact of Query Rewriting on Retriever Biases in RAG,” Findings ACL 2026. [ACL Anthology record](https://aclanthology.org/2026.findings-acl.414/), abstract lines 57–60.
- **Checked:** Five query enhancement methods across six retrievers; abstract reports simple LLM rewriting reduced aggregate bias by 54% but failed when biases combined adversarially, and effects varied substantially by retriever. Corroborating direct publisher abstract: Fayyaz et al., “Collapse of Dense Retrievers…,” ACL 2025, [record](https://aclanthology.org/2025.acl-long.447/), lines 58–60 reports short/early/repetition/literal preferences and downstream impact in its controlled dataset.
- **Supports / decision:** Treat retrieval ranking as a candidate-selection mechanism, not truth. Inspect result coverage and original passages; change vocabulary/domain/source route when observed results are skewed or irrelevant; seek a disconfirming route.
- **Does not establish:** That rewriting improves every search engine, that this live web tool uses a dense retriever, or that the abstract's reported figures transfer to this trial. I did not inspect full paper methods.

## E4 — Attribution/compression has measurable limits and contrary results

- **Source:** Wright et al., “Unstructured Evidence Attribution for Long Context Query Focused Summarization,” EMNLP 2025. [ACL Anthology record](https://aclanthology.org/2025.emnlp-main.95/), abstract lines 58–61. Short locator: “struggle to copy and properly cite unstructured evidence.” Reports five LLMs/four datasets and a synthetic training dataset (SUnsET).
- **Cross-check / conflict:** Buchmann et al., “Attribute or Abstain,” EMNLP 2024, [ACL record](https://aclanthology.org/2024.emnlp-main.463/), abstract lines 58–60 reports no lost-in-middle phenomenon for its attribution benchmark (six tasks/five models) but lower alignment between evidence and response quality for complex claims. Rahimi et al., Findings EMNLP 2025, [ACL record](https://aclanthology.org/2025.findings-emnlp.846/), lines 58–60 argues cross-encoder alignment changes prior position-bias conclusions. Ravaut et al., ACL 2024, [ACL record](https://aclanthology.org/2024.acl-long.153/), lines 58–60 studies six models, ten datasets, five metrics and proposes hierarchical/incremental summarization as tested mitigations.
- **Supports / decision:** Keep compact notes bound to original source, claim, version/date, passage locator, conditions, uncertainty/conflict, and relevance/next decision. Preserve competing evidence rather than compressing it away. Verify the original passage before relying on a summary.
- **Does not establish:** That one compression schema prevents omission/instruction contamination; the studies test attribution/summarization on their datasets, not this agent's notes. Results about position bias differ by task and metric, so “lost in middle” is not a universal property.

## E5 — Scope and telemetry limits

- **Observation:** This is one live, short research task using web search/open, with no controlled model comparison or repeated runs. Only abstracts were inspected for the cited papers; this web tool did not provide a persistent raw-response export or provider telemetry in the working record.
- **Decision:** Keep actual task observations and tool event count, but leave authenticated model, token use and cost null. Do not project reliability, savings or performance beyond this trial.
