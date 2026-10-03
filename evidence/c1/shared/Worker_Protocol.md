# Worker measurement instructions

The original immutable request and its work.prompt define your business task. Read only your own assigned source material, request, current public Forge skill and these observer instructions. No prior results, other samples, network, external business actions or sub-agents. Write only inside the assigned work.write_paths. Do actual work yourself; do not fabricate receipts or evidence.

Use the absolute capture.py path named in work.prompt. At task start record `worker_work` begin, and after your business JSON and Chinese explanation are written record `worker_work` end. Then record `worker_reply` begin. Commands are:

```
python3 CAPTURE mark --events ARTIFACTS/observations --actor worker --stage STAGE --event begin
python3 CAPTURE mark --events ARTIFACTS/observations --actor worker --stage STAGE --event end
python3 CAPTURE cli --record ARTIFACTS/logs/NEW.json --actor worker -- ACTUAL_COMMAND ARGUMENTS
```

Capture every invoked subprocess, including your business-output authoring command, reply construction and check-reply. Marker commands already create their own capture and need no extra cli wrapper. A persistent tool's file-write operations may not be subprocesses; disclose them rather than inventing a CLI count. All captured local commands and failures must remain. Keep final files unchanged after successful final preflight; if a correction is needed, preserve the rejected version and its capture before correcting, then capture the new preflight. At most two local correction attempts; no new worker.

Use only the assigned mode:

- **A/manual:** Manually author your own incomplete `worker-reply.draft.json` from the original request: exact host schema/job/attempt/request hash, null outer outcome/reason, actual in-scope artifact path/SHA refs. Project result is null. Package result has original invocation_id, null outcome, empty artifacts and evidence. Hashing/parsing with standard libraries and your own local script are allowed. Do not call `hostdraft reply`, `hostdraft decision`, `forge_template response` or another scaffold generator. Preserve your authoring source/capture.
- **B/draft:** Call the original `hostdraft.py reply --request REQUEST --artifact ACTUAL_JSON --artifact ACTUAL_MD --out ARTIFACTS/worker-reply.draft.json` through the capture wrapper. Use the default unchosen inner outcome (omit --flow-outcome), retain the generated incomplete draft.

Both modes independently fill a separate final assigned work.reply_path from actual business work. Project result is task-specific; package result has exactly invocation_id/outcome/artifacts/evidence from the original dispatch. Package inner artifacts contain business values, outer artifacts contain actual file refs. Do not put invocation_id in the host outer object.

**Both modes must invoke and capture `hostdraft.py check-reply --request REQUEST --reply ASSIGNED_REPLY` before ending worker_reply and returning your final message.** Success is only outer protocol validity, not business acceptance or host completion. Record worker_reply end after that capture; return actual reply and business file paths. If genuinely blocked, preserve partial records and report actual cause/next action. Do not silently substitute another treatment.
