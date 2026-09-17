# Acceptance record

## Scope and ownership

Baseline: 719d7ee3, clean before this change. User authorized proposal and implementation on 2026-09-17. No commit, push, deployment, production restart, indexing or research mutation is authorized by this change.

- gateway_ack (Terra high): Plugin invocation metadata and caller-facing ACK tests.
- skill_discovery (Terra high): Skill continuation/diagnostics and existing exploration guidance.
- lead: LSP failure fidelity, shared decisions, integration and final acceptance.

No nested delegation or additional reviewer. Workers return stable candidates; lead accepts exact diffs and proportionate checks.

## Evidence in progress

- Strict OpenSpec validation passed after planning.
- Ledger RED: `/tmp/webcodex-ledger-store-red.log`, expected `lsp_server_unavailable`, observed `runtime_error` (1 failing test).
- Initial runtime-test attempts exposed fixture setup and concurrent-edit compile failures; these are not product RED evidence. The fixture now uses the existing authorized StartSession path.
- Coordination adjustment: package writers initially overlapped a shared Cargo compilation window. Subsequent builds use an explicit single build owner and stable source windows; no second target directory or copied runner was introduced.

## Lead takeover

Both workers stopped because their provider usage limit was reached, not because their packages were accepted. The lead reconciled processes (no remaining Cargo/test process), retained all changes, and took sole write/build ownership.

The first ACK run reached the test and failed on a real contract mismatch: Plugin specialized governance does not consume context ACK, but the static declaration inherited the conservative accepting default. The lead aligned the declaration with existing specialized semantics rather than faking an ACK or weakening the assertion. Evidence: `/tmp/webcodex-ack-plugin-green.log` (despite its initial filename, this run failed).

Lead inspection also found that updating the `inspect` recommended flow alone did not change `tool_manifest(intent="exploration")`; the actual intent projection is now part of the same bounded fix and acceptance.

Runner diagnostics accept old reason-only payloads on the new Server. Structured diagnostics from the new Runner require the new Server; this is not a bidirectional rolling-compatibility claim. A later deployment must update Server and Runner together using the existing paired release/rollback procedure.

## Final local acceptance — lead-accepted

The lead reviewed the combined implementation and completed the worker packages. Provider-owned structured results are preserved, including absent structuredContent and colliding field names; wrapper attention is appended separately to provider content. Skill continuation is also declared in the output schema. Exploration changes affect the actual intent projection, not only its recommended-flow prose.

Sensitivity RED: deliberately disabling Plugin ACK extraction and returning only continuation arguments caused all three selected caller-facing tests to fail (`/tmp/webcodex-followups-sensitivity-red.log`). Both mutations were restored before GREEN. The final provider integration fixture required a stable managed user identity; this fixture correction did not relax production authorization.

Fresh GREEN receipts (Cargo +1.95.0):

| Command scope | Passed | Log |
| --- | ---: | --- |
| `-p webcodex --lib -- tool_runtime::tests::lsp tool_runtime::tests::skills mcp::tests::plugin_tools tool_runtime::tests::specialized_dispatch plugin_gateway::tests tool_runtime::specialized::tests` | 83 | `/tmp/webcodex-followups-final-root.log` |
| `-p webcodex-tool-contracts --lib` | 139 | `/tmp/webcodex-followups-contracts-final.log` |
| `-p webcodex-workflow-session --lib` | 183 | `/tmp/webcodex-ledger-store-green.log` |
| `-p webcodex-core --lib runner_skill` | 6 | `/tmp/webcodex-skill-core-green.log` |
| `-p webcodex-runner --bin webcodex-runner configured_skills` | 12 | `/tmp/webcodex-skill-runner-green.log` |

Total: 423 passing tests across these non-overlapping selections; no full-workspace or browser acceptance claim. Formatting (`cargo +1.95.0 fmt --all -- --check`), `git diff --check`, and strict OpenSpec validation passed. Temporary mutations are absent. Baseline HEAD remains unchanged; changes are uncommitted.

No push, release, Server/Runner restart, tunnel modification, production indexing or research mutation was performed. Local acceptance does not establish deployed browser acceptance. Publication remains a separate boundary; use the paired Server/Runner release and existing persistent `/data` lifecycle on deployment.
