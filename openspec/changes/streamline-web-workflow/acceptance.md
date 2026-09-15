# Fork acceptance

Status: candidate; deployment and release checks remain pending in tasks.md.

## Accepted source checks

- Initialization instructions: 3 tests passed; digest/size startup contract and schema tests passed.
- Startup/tool contracts: 132 tool-contract and 86 runtime-contract tests passed.
- Git hygiene: 16 tests passed, including bounded-output identity and incomplete-diagnostic regressions. The old sentinel-before-tracked-list ordering lost repository identity when the retained output tail exceeded its bound.
- Optional plugin: lead replay passed 9 tests. Concrete repair checks cover non-JUnit roots, UTF-16 entity declarations, and invalid UTF-8 continuation; no memory mutation API exists.
- Server library: 2640 passed, 0 failed, 2 intentionally ignored real-process tests. The two timeout/process-group tests were also run explicitly and passed.
- Runner: 844 passed, 0 failed, 4 intentionally ignored tests using Rust 1.95. Formatting and strict OpenSpec validation passed.
- Synchronous command fixture: a 20,000-byte stdout plus stderr case timed out before repair and passed after anonymous file-backed capture. This is a test-only change; production command execution is unchanged.
- Markdown links: 82 files, 529 links, zero missing local targets.

## Build prerequisites discovered

- Git 2.34 lacks the reviewed-commit attribute operation needed by current upstream. Git 2.55.0 passes the attribute probe; after upgrading, both reviewed-commit attribute regressions passed in the full Server suite.
- The host's default Rust 1.93 rejects an upstream test-only AtomicUsize::try_update call. Use the already-installed Rust 1.95 toolchain for Runner verification and release builds; do not patch production behavior to work around the compiler.

## Delivery boundary

This is a self-hosted Linux fork prerelease, not an upstream npm, Desktop, or six-platform release. The release must identify exact clean source, matching Server/Runner build identity, artifact checksums, isolated real-process smoke, and post-deploy MCP checks. Private operational logs/configuration and shared memory content are not release assets.
