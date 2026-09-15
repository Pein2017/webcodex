# Acceptance receipt

Status: implementation in progress. No release/deployment claimed yet.

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

## Remaining acceptance

Merged-source tests, clean release build, disposable real MCP smoke, fork push and
local deployment/rollback verification remain required. Path/status comparison is
not content auditing or Session authorship; no browser automatic wake is claimed.
