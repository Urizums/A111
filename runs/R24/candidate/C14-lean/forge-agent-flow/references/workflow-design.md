# Design from the outcome, not from a fixed roster

This reference is for tasks that genuinely need a reusable workflow, a substantial handoff or a revised process. It is not a mandatory planning form for ordinary requests.

First understand what the recipient is trying to accomplish and what they will receive. Then work backward through the decisions and information needed to produce it. Make consequential assumptions visible, especially permissions, sources, versions, units, deadline or platform. A sparse prompt still requires sensible domain judgment, but it does not authorize invented data, rules or success metrics.

## A workflow is a usable sequence of decisions

Explain where work begins, what changes at each meaningful step, what can happen when an input is missing or invalid, and what the next consumer needs. The representation is flexible: prose works for simple work; a compact diagram or node schema helps when there are multiple routes or execution machinery. Choose the format for the reader or runner, not to make the output look elaborate.

A receiving interface is useful when work crosses a boundary. It may need fields, units, source/version, allowed states and a check before the downstream step consumes it. If the work is all in one short context, an explicit schema may add nothing.

Before introducing parallel actors, ask whether their tasks are actually independent, whether their write domains overlap and who resolves conflicts. A separate actor can help with expertise or genuinely independent acceptance; additional role names alone do not confer either.

## Two illustrations of proportional design

**A direct extraction.** Someone asks for the date and city from a short, known document. Read the document, return those two values and check them against the source. A full coordinator/researcher/acceptor pipeline, persistent ledger and formal risk matrix would obscure the task.

**A comparison with required outputs.** Someone requests a 42-day forecast from methods A and B, then a recommendation. A usable design names the information available at forecast time, how both future tables are produced, how their outputs are compared and where the recommended method is chosen. Delivering only the selected table is not enough if both were requested. But there is no universal reason to require a third method, a particular forecasting model or a giant grid listing every row.

These examples illustrate how the decision follows the goal. They are not templates to copy into unrelated tasks.

## Choose checks before trusting results

For a substantive step, identify the original outcome it supports and an observation that could reject it. Test the main handoff and a relevant bad-input or boundary path. Keep the full delivery obligations visible even when the initial demonstration is smaller.

Distinguish a sound design from its implementation. A diagram can be logically coherent while the required browser, data, provider or resource is unavailable. An author stating that something passed is not the same as a receiving check, and a valid artifact is not proof of a broadly general method.

Adapt the process after evidence. If a task fails, repair the relevant decision or interface and test again without rewriting its original acceptance. If extra checks or actors do not change a consequential decision, remove them from the workflow rather than treating more process as better quality.

The workflow must be portable enough for its intended recipient to act without the designer's hidden context. It need not carry the repository's historical trials, controller scripts or research logs; those belong to the development workspace.
