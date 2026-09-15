import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const PROTOCOL_VERSION = "webcodex-plugin-v1";
const here = path.dirname(fileURLToPath(import.meta.url));
const pluginPath = path.join(here, "plugin.mjs");

function tempRoot() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "webcodex-web-workflow-"));
}

function writeExecutable(target, source) {
  fs.writeFileSync(target, source, { mode: 0o755 });
  fs.chmodSync(target, 0o755);
}

function createFixture() {
  const root = tempRoot();
  const project = path.join(root, "project");
  const memory = path.join(root, "memory");
  const outside = path.join(root, "outside");
  fs.mkdirSync(path.join(project, "reports"), { recursive: true });
  fs.mkdirSync(path.join(project, "src"), { recursive: true });
  fs.mkdirSync(path.join(project, "tests"), { recursive: true });
  fs.mkdirSync(path.join(memory, "rollouts"), { recursive: true });
  fs.mkdirSync(outside, { recursive: true });
  fs.writeFileSync(path.join(project, "src", "alpha.ts"), "export function alpha() {}\n");
  fs.writeFileSync(path.join(project, "src", "Beta.ts"), "export class Beta {}\n");
  fs.writeFileSync(path.join(project, "tests", "alpha.test.ts"), "test('alpha', () => {});\n");
  fs.writeFileSync(path.join(memory, "MEMORY.md"), "alpha memory line\nsecond line\n" + "z".repeat(200));
  fs.writeFileSync(path.join(memory, "rollouts", "one.jsonl"), '{"note":"alpha rollout"}\n');
  fs.writeFileSync(path.join(outside, "secret.md"), "alpha must not escape\n");
  fs.symlinkSync(path.join(outside, "secret.md"), path.join(memory, "linked-secret.md"));

  const codegraphEntry = path.join(root, "codegraph-entry.js");
  fs.writeFileSync(codegraphEntry, "// fake CodeGraph entry marker\n");
  const codegraphRuntime = path.join(root, "fake-codegraph-runtime.mjs");
  writeExecutable(
    codegraphRuntime,
    `#!/usr/bin/env node
const argv = process.argv.slice(2);
if (argv[0] !== "--liftoff-only" || argv[1] !== "--disable-warning=ExperimentalWarning") process.exit(9);
const command = argv.slice(3);
if (command[0] === "status") {
  process.stdout.write(JSON.stringify({
    initialized: true,
    version: "1.6.0-test",
    lastIndexed: "2026-09-15T00:00:00.000Z",
    pendingChanges: { added: 0, modified: 1, removed: 0 },
    worktreeMismatch: null,
    index: { state: "complete", reindexRecommended: false }
  }));
} else if (command[0] === "query") {
  let nodes = [
    { node: { name: "alpha", qualifiedName: "alpha", kind: "function", filePath: "src/alpha.ts", language: "typescript", startLine: 1, endLine: 1 }, score: 10 },
    { node: { name: "Beta", qualifiedName: "Beta", kind: "class", filePath: "src/Beta.ts", language: "typescript", startLine: 1, endLine: 1 }, score: 9 },
    { node: { name: "alpha test", qualifiedName: "alpha test", kind: "function", filePath: "tests/alpha.test.ts", language: "typescript", startLine: 1, endLine: 1 }, score: 8 }
  ];
  const kindAt = command.indexOf("--kind");
  if (kindAt >= 0) nodes = nodes.filter((item) => item.node.kind === command[kindAt + 1]);
  process.stdout.write(JSON.stringify(nodes));
} else {
  process.exit(8);
}
`,
  );
  const env = {
    ...process.env,
    WEBCODEX_WEB_WORKFLOW_PROJECTS_JSON: JSON.stringify({ fixture: project }),
    WEBCODEX_WEB_WORKFLOW_MEMORY_ROOT: memory,
    WEBCODEX_WEB_WORKFLOW_CODEGRAPH_RUNTIME: codegraphRuntime,
    WEBCODEX_WEB_WORKFLOW_CODEGRAPH_ENTRY: codegraphEntry,
    WEBCODEX_WEB_WORKFLOW_PYTHON: process.env.PYTHON || "python3",
  };
  return { root, project, memory, outside, env };
}

async function runProtocol(env, requests) {
  const child = spawn(process.execPath, [pluginPath], {
    stdio: ["pipe", "pipe", "pipe"],
    windowsHide: true,
    shell: false,
    env: { ...env, NODE_NO_WARNINGS: "1" },
  });
  child.stdout.setEncoding("utf8");
  child.stderr.setEncoding("utf8");
  let stdout = "";
  let stderr = "";
  child.stdout.on("data", (chunk) => {
    stdout += chunk;
  });
  child.stderr.on("data", (chunk) => {
    stderr += chunk;
  });
  for (const request of requests) child.stdin.write(`${JSON.stringify(request)}\n`);
  child.stdin.end();
  const exitCode = await new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      child.kill();
      reject(new Error("web-workflow protocol test timed out"));
    }, 15_000);
    child.once("exit", (code) => {
      clearTimeout(timer);
      resolve(code);
    });
  });
  assert.equal(exitCode, 0, stderr);
  assert.equal(stderr, "");
  const lines = stdout.split(/\r?\n/u).filter(Boolean);
  assert.equal(lines.length, requests.length, `unexpected protocol output: ${stdout}`);
  return lines.map((line) => JSON.parse(line));
}

function initialize(id = 1) {
  return { jsonrpc: "2.0", id, method: "initialize", params: { protocolVersion: PROTOCOL_VERSION } };
}

function listTools(id = 2) {
  return { jsonrpc: "2.0", id, method: "tools/list", params: {} };
}

function call(name, arguments_, id = 2) {
  return { jsonrpc: "2.0", id, method: "tools/call", params: { name, arguments: arguments_ } };
}

test("actual Plugin protocol exposes only configured bounded tools", async () => {
  const fixture = createFixture();
  try {
    const responses = await runProtocol(fixture.env, [initialize(), listTools()]);
    assert.equal(responses[0].result.protocolVersion, PROTOCOL_VERSION);
    assert.deepEqual(
      responses[1].result.tools.map((tool) => tool.name),
      ["pytest_report_summary", "memory_search", "memory_read", "codegraph_scoped_query"],
    );
    for (const tool of responses[1].result.tools) {
      assert.deepEqual(tool.annotations, {
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: false,
      });
      assert.equal(tool.inputSchema.additionalProperties, false);
    }
  } finally {
    fs.rmSync(fixture.root, { recursive: true, force: true });
  }
});

test("pytest summary preserves pass, failure, error, and skip counts without claiming execution", async () => {
  const fixture = createFixture();
  try {
    const report = `<?xml version="1.0"?>
<testsuites><testsuite name="suite">
  <testcase classname="pkg.test_mod" name="test_pass" />
  <testcase classname="pkg.test_mod" name="test_fail"><failure message="assert 1 == 2">trace</failure></testcase>
  <testcase classname="pkg.test_mod" name="test_error"><error message="fixture error">trace</error></testcase>
  <testcase classname="pkg.test_mod" name="test_skip"><skipped message="not supported" /></testcase>
</testsuite></testsuites>`;
    fs.writeFileSync(path.join(fixture.project, "reports", "junit.xml"), report);
    const [response] = await runProtocol(fixture.env, [
      call("pytest_report_summary", { project: "fixture", path: "reports/junit.xml", maxFailures: 1 }),
    ]);
    assert.equal(response.result.isError, false);
    assert.equal(response.result.structuredContent.testsExecuted, false);
    assert.equal(response.result.structuredContent.parserStatus, "parsed");
    assert.deepEqual(response.result.structuredContent.counts, {
      total: 4,
      passed: 1,
      failed: 1,
      errors: 1,
      skipped: 1,
    });
    assert.deepEqual(response.result.structuredContent.failures, [
      { identity: "pkg.test_mod::test_fail", kind: "failure", message: "assert 1 == 2" },
    ]);
    assert.equal(response.result.structuredContent.failuresTruncated, true);
    assert.deepEqual(response.result.structuredContent.source, {
      project: "fixture",
      root: fs.realpathSync(fixture.project),
      path: "reports/junit.xml",
    });
    assert.match(response.result.content[0].text, /no tests were executed/u);
  } finally {
    fs.rmSync(fixture.root, { recursive: true, force: true });
  }
});

test("pytest summary rejects malformed, unsafe, and oversized reports explicitly", async () => {
  const fixture = createFixture();
  try {
    fs.writeFileSync(path.join(fixture.project, "reports", "malformed.xml"), "<testsuite><testcase>");
    fs.writeFileSync(path.join(fixture.project, "reports", "not-junit.xml"), "<hello />");
    fs.writeFileSync(
      path.join(fixture.project, "reports", "unsafe.xml"),
      '<!DOCTYPE x [<!ENTITY y "boom">]><testsuite />',
    );
    fs.writeFileSync(
      path.join(fixture.project, "reports", "unsafe-utf16.xml"),
      Buffer.from(
        '<?xml version="1.0" encoding="UTF-16"?><!DOCTYPE testsuite [<!ENTITY x "expanded">]><testsuite><testcase name="&x;"/></testsuite>',
        "utf16le",
      ),
    );
    fs.writeFileSync(path.join(fixture.project, "reports", "large.xml"), Buffer.alloc(4 * 1024 * 1024 + 1, 32));
    const responses = await runProtocol(fixture.env, [
      call("pytest_report_summary", { project: "fixture", path: "reports/malformed.xml" }, 1),
      call("pytest_report_summary", { project: "fixture", path: "reports/not-junit.xml" }, 2),
      call("pytest_report_summary", { project: "fixture", path: "reports/unsafe.xml" }, 3),
      call("pytest_report_summary", { project: "fixture", path: "reports/unsafe-utf16.xml" }, 4),
      call("pytest_report_summary", { project: "fixture", path: "reports/large.xml" }, 5),
    ]);
    assert.equal(responses[0].result.isError, true);
    assert.equal(responses[0].result.structuredContent.errorCode, "malformed_xml");
    assert.equal(responses[1].result.structuredContent.errorCode, "not_junit_xml");
    assert.equal(responses[2].result.structuredContent.errorCode, "unsafe_xml");
    assert.equal(responses[3].result.structuredContent.errorCode, "unsafe_xml");
    assert.equal(responses[4].result.structuredContent.errorCode, "report_too_large");
  } finally {
    fs.rmSync(fixture.root, { recursive: true, force: true });
  }
});

test("memory search and byte-window read preserve provenance, bounds, and source bytes", async () => {
  const fixture = createFixture();
  try {
    const memoryPath = path.join(fixture.memory, "MEMORY.md");
    const before = fs.readFileSync(memoryPath);
    const responses = await runProtocol(fixture.env, [
      call("memory_search", { query: "alpha", maxResults: 10 }, 1),
      call("memory_read", { path: "MEMORY.md", maxBytes: 64 }, 2),
    ]);
    const search = responses[0].result;
    assert.equal(search.isError, false);
    assert.deepEqual(search.structuredContent.source, { root: fs.realpathSync(fixture.memory), path: "." });
    assert.deepEqual(
      search.structuredContent.matches.map((match) => match.path),
      ["MEMORY.md", "rollouts/one.jsonl"],
    );
    assert.equal(JSON.stringify(search).includes("must not escape"), false);
    assert.ok(search.structuredContent.bytesScanned <= 8 * 1024 * 1024);

    const read = responses[1].result;
    assert.equal(read.isError, false);
    assert.equal(read.structuredContent.actualOffset, 0);
    assert.equal(read.structuredContent.nextOffset, 64);
    assert.equal(read.structuredContent.eof, false);
    assert.equal(Buffer.byteLength(read.structuredContent.text, "utf8"), 64);
    assert.deepEqual(fs.readFileSync(memoryPath), before);
  } finally {
    fs.rmSync(fixture.root, { recursive: true, force: true });
  }
});

test("memory reads reject traversal and descendant symlinks without exposing outside content", async () => {
  const fixture = createFixture();
  try {
    const responses = await runProtocol(fixture.env, [
      call("memory_read", { path: "../outside/secret.md" }, 1),
      call("memory_read", { path: "linked-secret.md" }, 2),
    ]);
    assert.equal(responses[0].result.isError, true);
    assert.equal(responses[0].result.structuredContent.errorCode, "path_escape");
    assert.equal(responses[1].result.isError, true);
    assert.equal(responses[1].result.structuredContent.errorCode, "symlink_rejected");
    assert.equal(JSON.stringify(responses).includes("alpha must not escape"), false);
  } finally {
    fs.rmSync(fixture.root, { recursive: true, force: true });
  }
});

test("memory read rejects invalid UTF-8 at EOF and advances across a real split-codepoint boundary", async () => {
  const fixture = createFixture();
  try {
    fs.writeFileSync(path.join(fixture.memory, "invalid.txt"), Buffer.from([0xff]));
    fs.writeFileSync(path.join(fixture.memory, "boundary.txt"), `${"a".repeat(63)}🙂tail`);
    const responses = await runProtocol(fixture.env, [
      call("memory_read", { path: "invalid.txt", maxBytes: 64 }, 1),
      call("memory_read", { path: "boundary.txt", maxBytes: 64 }, 2),
      call("memory_read", { path: "boundary.txt", offset: 63, maxBytes: 64 }, 3),
    ]);

    const invalid = responses[0].result;
    assert.equal(invalid.isError, true);
    assert.equal(invalid.structuredContent.errorCode, "non_text_source");
    assert.equal(Object.hasOwn(invalid.structuredContent, "nextOffset"), false);

    const first = responses[1].result;
    assert.equal(first.isError, false);
    assert.equal(first.structuredContent.text, "a".repeat(63));
    assert.equal(first.structuredContent.nextOffset, 63);
    assert.equal(first.structuredContent.eof, false);

    const continuation = responses[2].result;
    assert.equal(continuation.isError, false);
    assert.equal(continuation.structuredContent.text, "🙂tail");
    assert.ok(continuation.structuredContent.nextOffset > first.structuredContent.nextOffset);
    assert.equal(continuation.structuredContent.eof, true);
  } finally {
    fs.rmSync(fixture.root, { recursive: true, force: true });
  }
});

test("CodeGraph query applies native kind plus explicit directory scope and reports freshness", async () => {
  const fixture = createFixture();
  try {
    const responses = await runProtocol(fixture.env, [
      call(
        "codegraph_scoped_query",
        { project: "fixture", search: "alpha", pathPrefix: "src", kind: "function", limit: 10 },
        1,
      ),
      call("codegraph_scoped_query", { project: "fixture", search: "alpha", limit: 10 }, 2),
    ]);
    const scoped = responses[0].result;
    assert.equal(scoped.isError, false);
    assert.deepEqual(scoped.structuredContent.results.map((item) => item.filePath), ["src/alpha.ts"]);
    assert.equal(scoped.structuredContent.pathPrefix, "src");
    assert.equal(scoped.structuredContent.kind, "function");
    assert.equal(scoped.structuredContent.complete, true);
    assert.equal(scoped.structuredContent.freshness.version, "1.6.0-test");
    assert.equal(scoped.structuredContent.freshness.pendingChanges.modified, 1);
    assert.match(scoped.content[0].text, /freshness warnings/u);

    const unscoped = responses[1].result;
    assert.equal(unscoped.isError, false);
    assert.deepEqual(
      unscoped.structuredContent.results.map((item) => item.filePath),
      ["src/alpha.ts", "src/Beta.ts", "tests/alpha.test.ts"],
    );
    assert.equal(unscoped.structuredContent.pathPrefix, null);
  } finally {
    fs.rmSync(fixture.root, { recursive: true, force: true });
  }
});

test("CodeGraph rejects unsupported file and escaping scopes instead of ignoring them", async () => {
  const fixture = createFixture();
  try {
    const responses = await runProtocol(fixture.env, [
      call("codegraph_scoped_query", { project: "fixture", search: "alpha", pathPrefix: "src/alpha.ts" }, 1),
      call("codegraph_scoped_query", { project: "fixture", search: "alpha", pathPrefix: "../outside" }, 2),
    ]);
    assert.equal(responses[0].result.isError, true);
    assert.equal(responses[0].result.structuredContent.errorCode, "unsupported_scope");
    assert.equal(responses[1].result.isError, true);
    assert.equal(responses[1].result.structuredContent.errorCode, "path_escape");
  } finally {
    fs.rmSync(fixture.root, { recursive: true, force: true });
  }
});

test("missing optional configuration omits capabilities and malformed configuration fails listing", async () => {
  const minimalEnv = { ...process.env };
  delete minimalEnv.WEBCODEX_WEB_WORKFLOW_PROJECTS_JSON;
  delete minimalEnv.WEBCODEX_WEB_WORKFLOW_MEMORY_ROOT;
  delete minimalEnv.WEBCODEX_WEB_WORKFLOW_CODEGRAPH_RUNTIME;
  delete minimalEnv.WEBCODEX_WEB_WORKFLOW_CODEGRAPH_ENTRY;
  const minimal = await runProtocol(minimalEnv, [listTools()]);
  assert.deepEqual(minimal[0].result.tools, []);

  const invalid = await runProtocol(
    { ...minimalEnv, WEBCODEX_WEB_WORKFLOW_PROJECTS_JSON: "not-json" },
    [listTools()],
  );
  assert.equal(invalid[0].error.code, -32603);
  assert.match(invalid[0].error.message, /WEBCODEX_WEB_WORKFLOW_PROJECTS_JSON/u);
});
