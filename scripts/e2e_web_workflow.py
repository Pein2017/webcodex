#!/usr/bin/env python3
"""Real full-operator Server + Runner smoke for the current Web workflow."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import signal
import socket
import subprocess
import sys
import tempfile
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


MAX_TIMEOUT_SECS = 300
RUNTIME_EXPOSURE = "full_operator_runtime"
RUNTIME_PROJECT = "agent:web-workflow-e2e:isolated"
REQUIRED_TOOLS = {
    "runtime_status",
    "list_projects",
    "work_on_project",
    "read_files",
    "apply_text_edits",
    "run_process",
    "run_job",
    "observe_jobs",
    "show_changes",
}


class Failure(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--server-bin", type=Path, default=root / "target/release/webcodex-server"
    )
    parser.add_argument(
        "--runner-bin", type=Path, default=root / "target/release/webcodex-runner"
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=Path("/tmp")
        / f"webcodex-e2e-web-workflow-{int(time.time())}-{os.getpid()}",
    )
    parser.add_argument("--timeout-secs", type=int, default=180)
    args = parser.parse_args()
    if not 1 <= args.timeout_secs <= MAX_TIMEOUT_SECS:
        parser.error(f"--timeout-secs must be between 1 and {MAX_TIMEOUT_SECS}")
    return args


def bounded(value: Any, limit: int = 1600) -> str:
    rendered = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return rendered if len(rendered) <= limit else rendered[:limit] + "...<truncated>"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Failure(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("WEBCODEX_")}
    env["RUST_LOG"] = "info"
    return env


def terminate_group(process: subprocess.Popen[bytes] | None) -> None:
    if process is None:
        return
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=3)
    else:
        process.wait()


def main() -> int:
    args = parse_args()
    started = time.monotonic()
    deadline = started + args.timeout_secs
    artifacts = args.artifact_dir.resolve()
    artifacts.mkdir(parents=True, exist_ok=False)
    smoke_path = artifacts / "e2e-web-workflow.log"
    server_path = artifacts / "server.log"
    runner_path = artifacts / "runner.log"
    receipt_path = artifacts / "receipt.json"
    checks: list[str] = []
    binaries: dict[str, Any] = {}
    server: subprocess.Popen[bytes] | None = None
    runner: subprocess.Popen[bytes] | None = None
    temp: tempfile.TemporaryDirectory[str] | None = None
    outcome = "failed"
    error_text: str | None = None

    with (
        smoke_path.open("w", encoding="utf-8") as smoke_log,
        server_path.open("wb") as server_log,
        runner_path.open("wb") as runner_log,
    ):
        def log(message: str) -> None:
            line = f"[e2e-web] {message}"
            print(line, flush=True)
            smoke_log.write(line + "\n")
            smoke_log.flush()

        def ok(message: str) -> None:
            checks.append(message)
            log(f"[ok] {message}")

        def remaining() -> float:
            seconds = deadline - time.monotonic()
            if seconds <= 0:
                raise Failure(f"overall timeout exceeded ({args.timeout_secs}s maximum)")
            return seconds

        def setup(argv: list[str], cwd: Path) -> None:
            try:
                subprocess.run(
                    argv,
                    cwd=cwd,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=min(15.0, remaining()),
                )
            except subprocess.CalledProcessError as exc:
                detail = exc.stderr.decode("utf-8", errors="replace")[-1000:]
                raise Failure(f"setup command {argv[0]} failed: {detail}") from exc

        def binary_identity(label: str, configured: Path) -> Path:
            path = configured.resolve()
            require(path.is_file() and os.access(path, os.X_OK), f"bad {label} binary: {path}")
            version = subprocess.run(
                [str(path), "--version"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=min(10.0, remaining()),
            ).stdout.strip()
            binaries[label] = {
                "path": str(path),
                "version": version,
                "sha256": sha256_file(path),
            }
            ok(f"{label} binary identity: {version}")
            return path

        try:
            server_bin = binary_identity("server", args.server_bin)
            runner_bin = binary_identity("runner", args.runner_bin)
            temp = tempfile.TemporaryDirectory(prefix="webcodex-e2e-web-workflow-")
            root = Path(temp.name)
            data = root / "data"
            registry = root / "project-registry"
            project = root / "project"
            for directory in (data, registry, project):
                directory.mkdir()

            original = "# Isolated Web Workflow\n\nstate: original"
            edited = "# Isolated Web Workflow\n\nstate: edited-and-validated"
            repository_guidance = (
                "REPOSITORY_GUIDANCE_SENTINEL_MUST_NOT_APPEAR_IN_DEFAULT_BOOTSTRAP\n"
            )
            guidance = (
                "DEDICATED_WEB_GUIDANCE_SENTINEL: use the configured Runner project "
                "and validate changes before completion."
            )
            (project / "README.md").write_text(original, encoding="utf-8")
            (project / "AGENTS.md").write_text(repository_guidance, encoding="utf-8")
            guidance_path = root / "mcp-instructions.md"
            guidance_path.write_text(guidance, encoding="utf-8")
            setup(["git", "init", "-b", "main"], project)
            setup(["git", "config", "user.email", "e2e@example.invalid"], project)
            setup(["git", "config", "user.name", "Web Workflow E2E"], project)
            setup(["git", "add", "README.md", "AGENTS.md"], project)
            setup(["git", "commit", "-m", "isolated fixture"], project)

            (registry / "isolated.toml").write_text(
                'id = "isolated"\n'
                f"path = {json.dumps(str(project))}\n"
                'name = "Isolated Web Workflow"\n'
                "allow_patch = true\n"
                'kind = "repo"\n',
                encoding="utf-8",
            )
            token = secrets.token_urlsafe(32)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(("127.0.0.1", 0))
                port = int(sock.getsockname()[1])
            runner_config = root / "runner.toml"
            runner_config.write_text(
                f'server_url = "http://127.0.0.1:{port}"\n'
                f"token = {json.dumps(token)}\n"
                'client_id = "web-workflow-e2e"\n'
                'display_name = "Web Workflow E2E"\n'
                'owner = "e2e"\n'
                f"project_registry_dir = {json.dumps(str(registry))}\n"
                "poll_interval_ms = 250\n"
                'transport = "websocket"\n\n'
                "[policy]\n"
                "allow_raw_shell = true\n"
                "allow_cwd_anywhere = false\n"
                f"allowed_roots = [{json.dumps(str(project))}]\n"
                "max_timeout_secs = 60\n"
                "max_output_bytes = 262144\n",
                encoding="utf-8",
            )

            server_env = clean_env()
            server_env.update(
                {
                    "WEBCODEX_ADDR": f"127.0.0.1:{port}",
                    "WEBCODEX_DATA": str(data),
                    "WEBCODEX_TOKEN": token,
                    "WEBCODEX_MCP_MODEL_SURFACE": "full-operator-v1",
                    "WEBCODEX_MCP_COMPACT_SCHEMAS": "false",
                    "WEBCODEX_MCP_INSTRUCTIONS_FILE": str(guidance_path),
                }
            )
            server = subprocess.Popen(
                [str(server_bin)],
                env=server_env,
                stdout=server_log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            while True:
                remaining()
                require(server.poll() is None, f"Server exited early ({server.returncode})")
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.1)
            ok(f"Server listening on isolated port {port}")
            runner = subprocess.Popen(
                [str(runner_bin), "--config", str(runner_config)],
                env=clean_env(),
                stdout=runner_log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )

            rpc_id = 0

            def rpc(method: str, params: Any) -> dict[str, Any]:
                nonlocal rpc_id
                rpc_id += 1
                payload = json.dumps(
                    {"jsonrpc": "2.0", "id": rpc_id, "method": method, "params": params},
                    separators=(",", ":"),
                ).encode()
                request = Request(
                    f"http://127.0.0.1:{port}/mcp",
                    data=payload,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    method="POST",
                )
                try:
                    with urlopen(request, timeout=min(10.0, remaining())) as response:
                        body = json.loads(response.read())
                except HTTPError as exc:
                    detail = exc.read().decode("utf-8", errors="replace")[-1200:]
                    raise Failure(f"HTTP {exc.code} for MCP {method}: {detail}") from exc
                except (URLError, OSError, json.JSONDecodeError) as exc:
                    raise Failure(f"MCP {method} transport failed: {exc}") from exc
                require(body.get("id") == rpc_id and "error" not in body, bounded(body))
                require(isinstance(body.get("result"), dict), bounded(body))
                return body["result"]

            def call(name: str, arguments: Any) -> Any:
                result = rpc("tools/call", {"name": name, "arguments": arguments})
                structured = result.get("structuredContent")
                require(
                    result.get("isError") is not True
                    and isinstance(structured, dict)
                    and structured.get("success") is True
                    and "output" in structured,
                    f"{name} failed: {bounded(result)}",
                )
                return structured["output"]

            initialized = rpc(
                "initialize", {"protocolVersion": "2025-06-18", "capabilities": {}}
            )
            require(
                initialized.get("serverInfo", {}).get("runtimeExposure")
                == RUNTIME_EXPOSURE
                and initialized.get("instructions") == guidance,
                f"initialize contract mismatch: {bounded(initialized)}",
            )
            ok("initialize returns configured guidance and full_operator_runtime identity")

            tools = rpc("tools/list", {}).get("tools")
            require(isinstance(tools, list), "tools/list omitted tools")
            by_name = {tool.get("name"): tool for tool in tools if isinstance(tool, dict)}
            require(not (REQUIRED_TOOLS - by_name.keys()), "required tools missing")
            require("job_tail" not in by_name, "ModelHidden job_tail was exposed")
            work = by_name["work_on_project"]
            work_props = work.get("inputSchema", {}).get("properties", {})
            require(
                work_props.get("include_project_instructions", {}).get("default") is False
                and work_props.get("include_workflow_guidance", {}).get("default") is False
                and work_props.get("include_extension_catalog", {}).get("default") is True
                and isinstance(work.get("outputSchema"), dict),
                "work_on_project schema defaults drifted",
            )
            observe = by_name["observe_jobs"]
            observe_input = observe.get("inputSchema", {})
            require(
                "items" in observe_input.get("required", [])
                and observe_input.get("properties", {}).get("wake_on", {}).get("enum")
                == ["change", "terminal"]
                and isinstance(observe.get("outputSchema"), dict),
                "observe_jobs schema drifted",
            )
            ok(f"tools/list exposes current full-operator contract ({len(by_name)} tools)")

            registered = None
            while registered is None:
                remaining()
                require(runner.poll() is None, f"Runner exited early ({runner.returncode})")
                projects = call("list_projects", {}).get("projects", [])
                registered = next(
                    (item for item in projects if item.get("id") == RUNTIME_PROJECT), None
                )
                if registered is None:
                    time.sleep(0.2)
            require(
                registered.get("capabilities", {}).get("git_available") is True,
                f"registered project was not identified as Git: {bounded(registered)}",
            )
            ok("real WebSocket Runner registered the isolated Git project")

            bootstrap = call(
                "work_on_project",
                {
                    "project": RUNTIME_PROJECT,
                    "instruction": "Edit README.md and validate the resulting state.",
                },
            )
            expected_guidance = {
                "revision": "sha256:" + hashlib.sha256(guidance.encode()).hexdigest(),
                "size_bytes": len(guidance.encode()),
            }
            sources = bootstrap.get("instructions", {}).get("sources")
            serialized = json.dumps(bootstrap, sort_keys=True)
            require(
                bootstrap.get("mcp_guidance") == expected_guidance
                and "workflow" not in bootstrap
                and isinstance(sources, list)
                and len(sources) == 1
                and isinstance(sources[0].get("fingerprint"), str)
                and "content" not in sources[0]
                and guidance not in serialized
                and repository_guidance.strip() not in serialized,
                f"default bootstrap guidance contract mismatch: {bounded(bootstrap)}",
            )
            ok("bootstrap defaults omit guidance bodies while preserving both identities")

            read = call(
                "read_files",
                {"project": RUNTIME_PROJECT, "items": [{"path": "README.md"}]},
            )
            item = read.get("items", [{}])[0]
            revision = item.get("output", {}).get("read_revision")
            require(
                item.get("output", {}).get("text") == original and isinstance(revision, int),
                f"read_files contract mismatch: {bounded(read)}",
            )
            edit = call(
                "apply_text_edits",
                {
                    "project": RUNTIME_PROJECT,
                    "changes": [
                        {
                            "kind": "edit",
                            "path": "README.md",
                            "expected_read_revision": revision,
                            "edits": [
                                {
                                    "kind": "replace_exact",
                                    "old_text": original,
                                    "new_text": edited,
                                }
                            ],
                        }
                    ],
                },
            )
            require(
                edit.get("state_changed") is True
                and edit.get("execution_state") == "completed"
                and (project / "README.md").read_text(encoding="utf-8") == edited,
                f"guarded edit failed: {bounded(edit)}",
            )
            ok("apply_text_edits changed README.md under its read_revision guard")

            validation = call(
                "run_process",
                {
                    "project": RUNTIME_PROJECT,
                    "executable": "python3",
                    "args": [
                        "-c",
                        "from pathlib import Path; assert 'state: edited-and-validated' "
                        "in Path('README.md').read_text(); print('sync-validation-ok')",
                    ],
                    "timeout_secs": 20,
                    "sync_wait_secs": 20,
                    "purpose": "test",
                    "assertion_name": "isolated README guarded edit validation",
                },
            )
            require(
                "sync-validation-ok" in str(validation.get("stdout_tail", ""))
                and "job_id" not in validation,
                f"run_process validation failed: {bounded(validation)}",
            )
            ok("run_process performed an actual successful validation command")

            job = call(
                "run_job",
                {
                    "project": RUNTIME_PROJECT,
                    "command": "printf 'async-log-start\\n'; sleep 1; "
                    "printf 'async-log-terminal\\n'",
                    "timeout_secs": 20,
                    "purpose": "operation",
                    "shell": "sh",
                },
            )
            job_id = job.get("job_id")
            require(isinstance(job_id, str) and job_id, f"run_job failed: {bounded(job)}")
            baseline = call(
                "observe_jobs", {"items": [{"job_id": job_id}], "tail_lines": 40}
            )
            first = baseline.get("items", [{}])[0]
            require(
                "output" not in first
                and first.get("job_id") == job_id
                and isinstance(first.get("observation_token"), str),
                f"stale observe_jobs projection: {bounded(baseline)}",
            )
            terminal = call(
                "observe_jobs",
                {
                    "items": [
                        {
                            "job_id": job_id,
                            "after_observation_token": first["observation_token"],
                        }
                    ],
                    "tail_lines": 40,
                    "wait_secs": 15,
                    "wake_on": "terminal",
                },
            )
            last = terminal.get("items", [{}])[0]
            output = str(first.get("stdout_tail", "")) + str(last.get("stdout_tail", ""))
            require(
                last.get("terminal") is True
                and last.get("status") == "completed"
                and last.get("exit_code") in (None, 0)
                and "async-log-start" in output
                and "async-log-terminal" in output,
                f"async Job lifecycle failed: {bounded([baseline, terminal])}",
            )
            ok("run_job reached terminal state and observe_jobs returned both log markers")

            changes = call("show_changes", {"project": RUNTIME_PROJECT})
            require(
                changes.get("clean") is False and "README.md" in json.dumps(changes),
                f"show_changes missed the edit: {bounded(changes)}",
            )
            ok("show_changes reports the guarded disposable repository edit")
            outcome = "passed"
            log(f"PASS: {len(checks)} checks in {time.monotonic() - started:.2f}s")
        except (Failure, OSError, subprocess.SubprocessError) as exc:
            error_text = str(exc)
            log(f"FAIL: {error_text}")
        finally:
            terminate_group(runner)
            terminate_group(server)
            if temp is not None:
                temp.cleanup()

    receipt: dict[str, Any] = {
        "schema_version": 1,
        "result": outcome,
        "runtime_exposure": RUNTIME_EXPOSURE,
        "runtime_project_id": RUNTIME_PROJECT,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "timeout_seconds": args.timeout_secs,
        "binaries": binaries,
        "checks": checks,
        "logs": {
            "smoke": str(smoke_path),
            "server": str(server_path),
            "runner": str(runner_path),
        },
    }
    if error_text is not None:
        receipt["error"] = error_text[:1600]
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(f"[e2e-web] receipt: {receipt_path}", flush=True)
    return 0 if outcome == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
