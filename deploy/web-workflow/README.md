# Self-hosted Web workflow

This fork keeps upstream runtime contracts and adds a small, optional Web workflow layer. The repository root `AGENTS.md` guides developers; the sibling [AGENTS.md](AGENTS.md) is the runtime instruction example.

## Configuration

Set `WEBCODEX_MCP_INSTRUCTIONS_FILE` on the Server to an operator-reviewed UTF-8 file (nonblank, at most 16 KiB). The Server loads it at startup and returns it in MCP initialization/discovery. `work_on_project` identifies the configured guidance without repeating its body. Restart after changing the file.

Configure shared skills on the Runner using an absolute operator-controlled directory:

```toml
[skills]
roots = ["/absolute/shared/skills"]
```

Use `skill_list` and `skill_read_file` or `context_request=["skills.catalog"]`; not every Codex skill is executable in this host. Memory reads and Python/CodeGraph helpers are provided by the optional [web-workflow plugin](../../plugins/web-workflow/README.md). Keep private roots and credentials outside this repository.

For normal work, select the exact registered Project in `work_on_project`, leave repository instruction injection disabled, then use current search/read/edit/validation tools. Retain the Session identifier for multi-step work. Jobs or tmux work are retrieved manually; no ChatGPT auto-wake integration is provided.

Use `recording_session_id` explicitly for recorded calls. `read_files` returns a
`read_revision` that can be copied directly to `apply_text_edits` as
`expected_read_revision`; callers do not translate it into a SHA. Discover current
schemas and inspect the selected Runner's capabilities when a script language is
unavailable. JS/TS also require a suitable Node runtime on that Runner.

Startup/finish workspace observations distinguish pre-existing dirty paths from
later path/status changes. These are bounded Git observations, not filesystem
auditing or proof of Session authorship. Already-dirty overlap does not prove
unchanged contents, and failed/incomplete observations cannot prove absence.
`write_like` counts tool classes, so zero does not mean a shell made no writes.

For generic test execution, use `purpose=test` and a stable `assertion_name` for
the same validation across fixes. A later matching PASS can resolve a prior failed
assertion; unrelated success cannot clear a real execution failure. Declare
expected negative results before execution. Test counts from supported summaries
remain separate from exit status, completeness and scientific acceptance. The
optional JUnit report reader still never executes tests.

Pytest count evidence from a direct typed `run_process` invocation uses reported `passed + failed` for
`tests_run_count`; skips, collection/fixture errors and deselection are not
silently counted as passes or failures. Unsupported or incomplete summaries keep
counts unknown. Use the existing JUnit reader for the report's separate skipped
and error counts, and retain actual execution evidence for acceptance.
Raw shell/script previews do not establish pytest executable identity and do not
gain this new count parser merely by printing a pytest-like summary.

For an asynchronous `run_process` Job that belongs in Session closeout, explicitly
pass the supported business `session_id` as well as `recording_session_id`.
The former binds the Job through normal Session authorization; the latter records
the call but does not grant Job ownership. The smoke retains an outer-recorder-only
synchronous test and uses explicit business ownership for its asynchronous test.

The merged upstream Git review path requires Git with `check-attr --source` support. Verify `git check-attr --source=HEAD binary -- README.md` in this checkout before deployment; an older system Git can silently lose reviewed-commit attribute evidence. Use an operator-managed Git installation on the Server/Runner wrapper PATH (for example, the selected Conda environment), and verify the effective runtime executable. Python report parsing requires Python 3 and the optional plugin requires Node.js 18+; CodeGraph uses its existing operator-installed runtime.

## Fork maintenance and delivery

- `upstream` is the original WebCodex repository; `origin` is the operator's fork.
- Use scoped development branches and commits with repository-local OpenSpec changes. This fork uses `coordexp/*` because its inherited `codex` branch prevents a `codex/*` ref namespace. Merge upstream before accepting an update, preserving the original history and local patches.
- Fork deployment tags use `coordexp-YYYY.MM.DD.N`. These are self-hosted Linux prereleases, not upstream npm/desktop/container releases. The upstream package version remains visible alongside the exact Git commit and dirty flag.
- The inherited container-release workflow skips `coordexp-*` tags; creating a fork prerelease does not authorize container or npm publication.
- Before deployment: focused changed-contract tests, optional-plugin tests, strict OpenSpec validation, and a disposable real Server/Runner smoke. Build both binaries from the same clean commit using `release`; record checksums and actual build identities.
- Retain old binaries, operator config and a consistent Server-state backup. Check active jobs before restarting the existing Server/Runner. A schema migration may require restoring the matching backup when rolling back.
- Publish only reviewed source and Linux artifacts with scope/validation notes to the fork. Do not invoke upstream package publication workflows. Never publish private configuration, memory content or operational credentials.
- After deployment, verify MCP initialization, effective guidance identity, all registered projects, shared context, and the edit/test path on a disposable project. Refresh the ChatGPT connection when tool metadata changes, then start a new conversation if it retained old schemas.

The fork's focused real-entry smoke uses only disposable state and the selected binaries:

```bash
python3 scripts/e2e_web_workflow.py \
  --server-bin target/release/webcodex-server \
  --runner-bin target/release/webcodex-runner \
  --artifact-dir /absolute/private/verification-output \
  --timeout-secs 300
```

It checks current full-operator MCP contracts, guarded edits, actual command validation, and asynchronous Job terminal/log observation. Preserve its receipt and logs outside the public release assets. It does not claim to test ChatGPT's browser UI or the separate Actions surface.
