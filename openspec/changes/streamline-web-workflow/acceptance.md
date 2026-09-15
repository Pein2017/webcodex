# Fork acceptance

Status: candidate; deployment and release checks remain pending in tasks.md.

## Accepted source checks

- Initialization instructions: 3 tests passed; digest/size startup contract and schema tests passed.
- Startup/tool contracts: 132 tool-contract and 86 runtime-contract tests passed.
- Git hygiene: 16 tests passed, including bounded-output identity and incomplete-diagnostic regressions. The old sentinel-before-tracked-list ordering lost repository identity when the retained output tail exceeded its bound.
- Optional plugin: lead replay passed 11 tests. Concrete repair checks cover non-JUnit roots, UTF-16 entity declarations, invalid UTF-8 continuation, and the admitted Native Plugin schema subset; no memory mutation API exists. Native admission rejects numeric bounds/pattern schema keywords, so descriptions state bounds while unchanged runtime validation enforces them.
- Server library: 2640 passed, 0 failed, 2 intentionally ignored real-process tests. The two timeout/process-group tests were also run explicitly and passed.
- Runner: 844 passed, 0 failed, 4 intentionally ignored tests using Rust 1.95. Formatting and strict OpenSpec validation passed.
- Synchronous command fixture: a 20,000-byte stdout plus stderr case timed out before repair and passed after anonymous file-backed capture. This is a test-only change; production command execution is unchanged.
- Markdown links: 82 files, 529 links, zero missing local targets.

## Real-entry evidence

- Lead replay of `scripts/e2e_web_workflow.py` passed 11 checks against clean release binaries: real WebSocket registration, configured MCP instructions, current schemas, guarded edit, actual structured validation, asynchronous Job terminal/log observation, and Git change readback. The script terminates only its own process groups and removes its disposable workspace.
- The old `e2e_zero_config_ws.sh` did not pass. Its consumer assertions assume obsolete Actions/adaptive schemas and `observe_jobs` nesting. Current model-facing Job items expose status/log fields directly, not under a nested `output`; the new live smoke proves that equivalent lifecycle rather than suppressing its check.
- Initial deployed checks passed: matching clean Server/Runner identity, three online Projects, unchanged authenticated exposure, and the same 3033-byte guidance hash through initialize and server/discover. All three real worktrees report `git_available=true`.
- Live Native Plugin admission passed for all three configured provider instances. A real pytest report preserved 1 pass, 1 failure, 1 skip and `testsExecuted=false`. Shared memory search/read returned bounded source-provenanced results. Scoped CodeGraph returned a symbol inside the requested research directory with freshness and truncation metadata.
- Main/infra currently have no CodeGraph CLI index; the scoped adapter reports `codegraph_uninitialized` rather than fabricating results. Research and the WebCodex source checkout have indexes; existing CodeGraph access remains installed.
- The external WebCodex connector successfully returned deployed runtime status and 36 shared Runner Skills for the research worktree. Main-project shared-Skill acceptance remains pending the symlink-source isolation repair.

## Build prerequisites discovered

- Git 2.34 lacks the reviewed-commit attribute operation needed by current upstream. Git 2.55.0 passes the attribute probe; after upgrading, both reviewed-commit attribute regressions passed in the full Server suite.
- The host's default Rust 1.93 rejects an upstream test-only AtomicUsize::try_update call. Use the already-installed Rust 1.95 toolchain for Runner verification and release builds; do not patch production behavior to work around the compiler.

## Delivery boundary

This is a self-hosted Linux fork prerelease, not an upstream npm, Desktop, or six-platform release. The release must identify exact clean source, matching Server/Runner build identity, artifact checksums, isolated real-process smoke, and post-deploy MCP checks. Private operational logs/configuration and shared memory content are not release assets.
