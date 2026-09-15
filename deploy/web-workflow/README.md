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

The merged upstream Git review path requires Git with `check-attr --source` support. Verify that command against a known commit before deployment; an older system Git can silently lose reviewed-commit attribute evidence. A private Git installation on the Server/Runner wrapper PATH keeps this dependency separate from other applications. Python report parsing requires Python 3 and the optional plugin requires Node.js 18+; CodeGraph uses its existing operator-installed runtime.

## Fork maintenance and delivery

- `upstream` is the original WebCodex repository; `origin` is the operator's fork.
- Use scoped development branches and commits with repository-local OpenSpec changes. This fork uses `coordexp/*` because its inherited `codex` branch prevents a `codex/*` ref namespace. Merge upstream before accepting an update, preserving the original history and local patches.
- Fork deployment tags use `coordexp-YYYY.MM.DD.N`. These are self-hosted Linux prereleases, not upstream npm/desktop/container releases. The upstream package version remains visible alongside the exact Git commit and dirty flag.
- Before deployment: focused changed-contract tests, optional-plugin tests, strict OpenSpec validation, and a disposable real Server/Runner smoke. Build both binaries from the same clean commit using `release`; record checksums and actual build identities.
- Retain old binaries, operator config and a consistent Server-state backup. Check active jobs before restarting the existing Server/Runner. A schema migration may require restoring the matching backup when rolling back.
- Publish only reviewed source and Linux artifacts with scope/validation notes to the fork. Do not invoke upstream package publication workflows. Never publish private configuration, memory content or operational credentials.
- After deployment, verify MCP initialization, effective guidance identity, all registered projects, shared context, and the edit/test path on a disposable project. Refresh the ChatGPT connection when tool metadata changes, then start a new conversation if it retained old schemas.
