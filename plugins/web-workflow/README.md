# Web workflow Native Tool Plugin

This optional, read-only provider adds bounded projections that are useful from
ChatGPT Web without introducing another test runner, memory store, or CodeGraph
service:

- `pytest_report_summary` parses an existing pytest JUnit XML report. It never
  invokes pytest and returns `testsExecuted: false` alongside pass, failure,
  error, and skip counts.
- `memory_search` and `memory_read` inspect one explicitly configured shared
  memory root. They do not write, synchronize, copy, or import memory into a
  project.
- `codegraph_scoped_query` invokes an existing CodeGraph CLI. Its native
  `query --json --kind --limit` options are preserved; because CodeGraph 1.6 has
  no query path filter, this adapter applies an optional directory prefix to a
  bounded candidate set and reports when that set is not exhaustive.

All returned sources include their configured root and relative path or project
id. Paths are canonicalized under configured roots, traversal is rejected, and
descendant symlinks are never followed. This is a trusted local executable, not
a filesystem sandbox.

## Operator configuration

Configuration is environment-only. Do not add machine paths or memory content
to this repository. A dedicated shell profile can carry the variables into the
provider's prepared environment:

```toml
[shell.profiles.web-workflow]
program = "sh"
args = ["-c"]

[shell.profiles.web-workflow.env]
WEBCODEX_WEB_WORKFLOW_PROJECTS_JSON = '''{"project-a":"/absolute/project/a","project-b":"/absolute/project/b"}'''
WEBCODEX_WEB_WORKFLOW_MEMORY_ROOT = "/absolute/read-only/codex-memory-root"
WEBCODEX_WEB_WORKFLOW_CODEGRAPH_RUNTIME = "/absolute/codegraph/runtime"
WEBCODEX_WEB_WORKFLOW_CODEGRAPH_ENTRY = "/absolute/codegraph/cli-entry.js"
WEBCODEX_WEB_WORKFLOW_PYTHON = "python3"

[plugins]
request_timeout_secs = 120

[[plugins.providers]]
id = "web-workflow"
name = "Web workflow"
command = "node"
args = ["/absolute/webcodex/plugins/web-workflow/plugin.mjs"]
cwd = "/absolute/project/a"
profile = "web-workflow"
timeout_secs = 120
```

`WEBCODEX_WEB_WORKFLOW_PROJECTS_JSON` is an object from stable, non-sensitive
operator ids to absolute authorized project roots. It enables JUnit summaries;
CodeGraph access additionally requires both CodeGraph variables.
`WEBCODEX_WEB_WORKFLOW_MEMORY_ROOT` independently enables the two memory tools.
`WEBCODEX_WEB_WORKFLOW_PYTHON` is optional and defaults to `python3`.

Omit an optional capability's variables to omit its tools from the provider
catalog. A partially specified or malformed capability configuration makes
`tools/list` fail so `plugin_tool check` cannot advertise a misleading ready
provider.

`work_on_project` exposes only providers whose configured `cwd` resolves to that
project's authoritative root. If this provider should be discoverable from
several registered projects, configure one provider instance per project with
that project's exact `cwd` (and a unique provider id). Those instances may all
point to this same executable and the same operator-configured memory root; no
memory copy is required.

After editing `runner.toml`, use the normal bounded lifecycle:

```text
plugin_tool(action="check", runner="RUNNER", plugin="web-workflow")
plugin_tool(action="reload", runner="RUNNER")
plugin_tool(action="list", runner="RUNNER", plugin="web-workflow")
```

Changing Plugin configuration does not require a Runner process restart. Do not
remove or replace an existing CodeGraph provider: this provider is additive, so
its existing unscoped tools continue to work.

## Bounds and semantics

- JUnit input is limited to 4 MiB. DTD/entity declarations, non-JUnit roots,
  and malformed XML are rejected, and at most 25 failing identities are
  returned. A successfully parsed report can still describe failed tests
  without making the tool call itself an error.
- Memory reads return at most 32 KiB per call with an exact continuation byte
  offset. Search examines at most 512 files, 1 MiB per file, and 8 MiB total;
  all ceilings and incomplete results are returned explicitly.
- CodeGraph requests time out before the recommended 120-second Plugin timeout.
  Scoped search considers at most 1000 native query candidates and returns at
  most 50 symbols. Index timestamp, pending changes, mismatch, state, and
  reindex recommendation accompany each result.
- CodeGraph scope is exactly a live project-relative directory prefix. File,
  glob, language, and arbitrary expression scopes are unsupported. `kind` is
  supported because it is a real CodeGraph query option.

The Plugin is read-only, but it executes trusted local Python and CodeGraph
programs supplied by the operator. Existing WebCodex Plugin admission,
permissions, bindings, process ownership, and output limits remain authoritative.

## Development check

The test suite uses disposable projects, reports, memory, symlink escapes, and a
fake CodeGraph CLI at the same argv/protocol boundary:

```bash
cd plugins/web-workflow
npm test
```

The tests require Node.js 18+ and Python 3. No package installation is needed.
