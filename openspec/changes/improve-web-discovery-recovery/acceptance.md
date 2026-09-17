# Acceptance record

Status: implementation in progress; no deployment acceptance yet.

## Trace assessment

Source: user-uploaded `tool-call-data (3).json`, 46 calls. This record intentionally excludes raw research code, command output and opaque Session/binding ids.

- Skill: one successful complete definition read; no Skill ID schema rejection.
- CodeGraph: three successful scoped calls, returning 5/5/1 symbols with complete/current index reports. One earlier describe used `client_id` instead of `runner`, then recovered.
- Execution: one shell timeout confirmed by the Session ledger, although its direct exported output is null. The script compared long AST strings pairwise; no timing profile proves its exact hotspot. Do not infer disconnect or safe retry.
- Continuity: 11 unacknowledged hints; one explicitly partial handoff cannot establish a baseline. Recorder and business Session fields are inconsistently supplied, including one malformed read Session string. No authority exploit is demonstrated by the export.
- Completeness: one batch read hits the response budget; eight read calls have at least one partial file and a suggested continuation. Partial files do not by themselves require reading every remaining line. One large process diff has stdout truncation. Later targeted reads show recovery of some relevant excerpts, so missing full-file continuation is not by itself proof of an invalid final review.
- No final review or Session close is in the export. Do not infer a leak, completed audit, or scientific conclusion.

## RED evidence

- `/tmp/webcodex-discovery-recovery-red.log`: exact complete-handoff argument assertion fails against prior producer (1 failed).
- `/tmp/webcodex-discovery-catalog-red.log`: startup selected and configured Skill follow-ups absent (2 failed).
- `/tmp/webcodex-discovery-plugin-red.log`: exact Runner/provider describe follow-up absent (1 failed).
- `/tmp/webcodex-discovery-e2e-red/receipt.json`: old dogfood real stateless MCP fails at startup Skill follow-up project/revision check, after normal Runner/project startup succeeds.

## Ownership

- Terra recovery: session_context producer + focused contract assertion; stable/race/recorder guards retained.
- Terra discovery: startup Skill/Plugin producers and catalog/consumer tests.
- Lead: guidance, real MCP test extension, exact diff review, serialized Cargo verification, fork publication and local deployment.

No nested delegation, new controller, timeout waiver, auto-ACK or automatic indexing.

## Focused GREEN

- Startup/work_on_project: 38 passed; catalog byte/prefix/UTF-8/unavailable contracts: 4 passed.
- Session context suite: 14 passed, including real HTTP returned-suggestion recovery and stable/race/recorder fences.
- Lead corrected two historical exact-shape assertions revealed by the broader focused recovery run (12 pass/2 fail before correction); it now replays returned arguments rather than a separately handcrafted default handoff.
- Rust formatting, Python compilation and strict OpenSpec validation passed. Live deployment and the updated disposable binary E2E remain pending.

## Deployment amendment

The user explicitly added /data-only persistence while verification was underway. Read-only process/dependency audit preserved all services. Existing binaries, native Node/CodeGraph and Tunnel client are already persistent; operator config, credentials, SQLite/Session state and receipts are not. System Git 2.34.1 rejects `check-attr --source=HEAD`; existing ms Git 2.55.0 passes. System Python 3.10 can run the stdlib JUnit helper.

The preceding `.09.16.2` installation omitted `pytest_report.py` despite source retaining it unchanged. The new bundle must include it and verify actual parsing. A separately named rollback bundle may retain the old binaries with that exact unchanged helper; the original release remains untouched.
