# Acceptance receipt

Status: implementation and disposable release acceptance passed; fork publication and local activation pending.

## Source and scope

- Initial checkout: `coordexp/web-workflow` at `47bf37df`; fork `Pein2017/webcodex`, upstream `yyjeqhc/webcodex`.
- Planning: `6e7cfd3e`; guidance: `edaa9fe0`. Strict OpenSpec validation passed before implementation.
- Upstream fetched at assessment: `6a1433d0`, four incoming commits; refreshed to `01dc7d31` (one additional execution-guidance update) and merged as `0c660be3`. Seven ordinary overlapping files were reconciled: compact IDs, under-lock allocation, additive baseline fields, fixture identity, opt-in guidance prose, and the existing bounded SSH shutdown check. No authority or instruction-default change was accepted.
- Current deployed baseline observed: clean matching Server/Runner `b0edfa887a83`, four online Projects, no active Jobs.

## Evidence retained

- Live stateless MCP discovery declares all five script languages. Existing source implements `read_revision`-to-SHA guarding; no second fence/schema registry added.
- Pytest RED: validation evidence expected `tests_detected=true`, got null; generic execution expected true, got false. Both reached the target assertions and exited 101 on the pre-fix implementation. GREEN: parser 3, validation/recovery 5, typed execution 5, output-schema 1 tests passed under Rust 1.95.0. Implementation commit: `3f07e8ab`.
- Baseline GREEN: persistence/resume/legacy 2, real startup/finish and bounded comparisons 6, existing startup projections 6 tests passed. Lead reviewed persistence, raw Git capture, completeness and public projection boundaries. Implementation commit: `502a1f1f`.
- Existing optional Native Plugin suite: 11 passed, 0 failed. Its source/dependencies are unchanged. Raw log remains operator-local under this deployment's verification directory.
- Guidance: 5371 UTF-8 bytes (below 16 KiB); initial Markdown local-link check passed (88 files, 529 links, zero missing targets).
- First integrated root run: 2655 passed, 2 failed, 2 ignored. One fork-only Skill fixture still used the upstream-retired hexadecimal ID; its isolated failure reproduced, then passed with the actual compact ID format and unchanged behavioral assertions. The other failure exceeded existing startup budgets by 41/40 bytes; shorten only the context-sidecar prose by 42 bytes and retain both original budgets. Final integrated GREEN remains required.
- The four implementation package suites passed before merge: Core 252, Tool Contracts 132, Validation 97, Workflow Session 178. Post-merge optional plugin tests passed 11/11; strict OpenSpec and local Markdown links passed (90 files, 529 links).
- Integrated suites subsequently passed 4537 tests (6 intentionally ignored). The final guidance keeps upstream's tested ordering/role language and saves 50 bytes without raising startup budgets. A production-only build failure exposed a test-gated constant re-export; `5a5b9949` corrects that visibility, and the clean release build passed.
- Real stateless MCP evidence passed JS, revision-guarded edit/stale rejection, baseline comparison, synchronous fail/fix/pass, and async pytest Job counts. It then exposed missing synchronous PASS counts in the outer Session ledger despite correct public counts. A matching kernel caller fixture reproduced this (exit 101), then passed after deferring process/script compaction until after the canonical outer recorder. No inferred exit code, new wire field, hidden recorder, or assertion-budget relaxation was introduced. Final rebuilt real-MCP GREEN remains required.

## Final candidate acceptance

- Clean binary source: `69f0273dcf80e1232f7a22e0e7f77c5778d1c447`, upstream `01dc7d31` included. Both release binaries report `dirty=false`, version `0.4.1`, and the same source/built-at identity.
- Server suite after the recorder fix: 2658 passed, 2 ignored. Unchanged package/Runner suites contribute 1880 passed, 4 ignored: total 4538 passed, 6 intentionally ignored. Optional Native Plugin tests: 11 passed.
- Real stateless MCP smoke: 25 checks passed in 7.22 seconds (7.369 seconds including cleanup), fixture resources removed. Operator-local receipt: `verification/coordexp-2026.09.15.2/e2e-owned-async/receipt.json`.
- Async Job ownership remains explicit: a supported business `session_id` is required in addition to `recording_session_id` for Session-owned closeout. No runtime authority change was made. The synchronous regression remains outer-recorder-only.
- Server SHA-256: `93336d8409e13cd59e9bbbdade9e493195db6d02f048eb25ff39c0f799e4ce6e`.
- Runner SHA-256: `04fa884fed87bbaece083c1e6546436e2c720837e1ba852c5bce00f3fb2baa74`.
- Final operator guidance: 5527 UTF-8 bytes, SHA-256 `30fc7b623263919e2ecf8e225b0e7dbef405733d9bf9604348ca64b5988c05e2`. The final guidance/smoke clarification does not alter compiled Rust source.

Fork push and local deployment/rollback verification remain required. Path/status
comparison is not content auditing or Session authorship; no browser automatic
wake or ChatGPT UI acceptance is claimed.
