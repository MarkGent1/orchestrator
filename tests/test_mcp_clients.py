import asyncio
import sys
import time
from pathlib import Path

import pytest

import mcp_servers.ado_mcp_client as ado_module
import mcp_servers.github_mcp_client as github_module
from mcp_servers.ado_mcp_client import AdoMcpClient
from mcp_servers.github_mcp_client import GithubMcpClient

FAKE_SERVER = Path(__file__).parent / "fixtures" / "fake_mcp_server.py"


def _patch_to_fake_server(monkeypatch, module, scenario):
    """
    Both clients spawn `["node", server_path]`. Swap that for our
    Python fake server so these tests exercise the real
    subprocess/pipe/timeout handling without depending on Node.js
    being installed. Every other subprocess.Popen kwarg (pipes, env,
    bufsize) is passed through unchanged.
    """
    real_popen = module.subprocess.Popen

    def fake_popen(argv, **kwargs):
        return real_popen([sys.executable, str(FAKE_SERVER), scenario], **kwargs)

    monkeypatch.setattr(module.subprocess, "Popen", fake_popen)


async def _call_then_close(client, method, params):
    """
    Runs client._call(...) and client.close() inside the SAME
    asyncio.run() invocation. This matters: asyncio.run() waits for
    any outstanding loop.run_in_executor() work (here, the background
    thread blocked on proc.stdout.readline()) to finish before it
    returns, as part of its own shutdown_default_executor() cleanup.
    If close() (which terminates the child process and unblocks that
    read) were called *after* asyncio.run() returns -- as a real
    caller naturally would, in a separate statement -- a timed-out or
    hung call would deadlock the test forever waiting for a thread
    that only unblocks once the very close() call it's waiting to
    reach finally runs. Production code (main.py) doesn't hit this
    because ado.close()/github.close() run inside the same long-lived
    event loop's finally block, before that single asyncio.run(main())
    call ever tears down.
    """
    try:
        return await client._call(method, params)
    finally:
        client.close()


@pytest.mark.parametrize("module,client_cls", [
    (ado_module, AdoMcpClient),
    (github_module, GithubMcpClient),
])
class TestSharedTransportBehavior:
    """Low-level _call()/close() behavior is identical between the two clients."""

    def test_call_returns_result_on_success(self, monkeypatch, module, client_cls):
        _patch_to_fake_server(monkeypatch, module, "echo")
        monkeypatch.setenv("FAKE_WRAP_KEY", "echoed")
        client = client_cls("unused-server-path.js", timeout=5)
        result = asyncio.run(_call_then_close(client, "someMethod", {"a": 1}))
        assert result["structuredContent"]["echoed"] == {"a": 1}

    def test_noisy_stderr_does_not_deadlock(self, monkeypatch, module, client_cls):
        """
        Regression test: without draining stderr in a background
        thread, a chatty child process can fill the OS pipe buffer and
        block on write, which then blocks the parent's stdout read
        forever with no visible error.
        """
        _patch_to_fake_server(monkeypatch, module, "noisy")
        client = client_cls("unused-server-path.js", timeout=10)
        result = asyncio.run(_call_then_close(client, "someMethod", {"a": 1}))
        assert "structuredContent" in result

    def test_hang_times_out_instead_of_blocking_forever(self, monkeypatch, module, client_cls):
        _patch_to_fake_server(monkeypatch, module, "hang")
        client = client_cls("unused-server-path.js", timeout=0.5)
        with pytest.raises(RuntimeError, match="Timed out"):
            asyncio.run(_call_then_close(client, "someMethod", {}))

    def test_crash_mid_call_reported_clearly(self, monkeypatch, module, client_cls):
        _patch_to_fake_server(monkeypatch, module, "crash")
        client = client_cls("unused-server-path.js", timeout=5)
        with pytest.raises(RuntimeError):
            asyncio.run(_call_then_close(client, "someMethod", {}))

    def test_dead_on_arrival_reported_before_first_call(self, monkeypatch, module, client_cls):
        _patch_to_fake_server(monkeypatch, module, "dead_on_arrival")
        client = client_cls("unused-server-path.js", timeout=5)
        time.sleep(0.3)  # give the child a moment to actually exit
        with pytest.raises(RuntimeError):
            asyncio.run(_call_then_close(client, "someMethod", {}))

    def test_close_terminates_process(self, monkeypatch, module, client_cls):
        _patch_to_fake_server(monkeypatch, module, "hang")
        client = client_cls("unused-server-path.js", timeout=5)
        assert client.proc.poll() is None
        client.close()
        assert client.proc.poll() is not None

    def test_close_is_safe_to_call_twice(self, monkeypatch, module, client_cls):
        _patch_to_fake_server(monkeypatch, module, "hang")
        client = client_cls("unused-server-path.js", timeout=5)
        client.close()
        client.close()  # must not raise


async def _get_work_item_then_close(client, id):
    try:
        return await client.get_work_item(id)
    finally:
        client.close()


async def _create_child_task_then_close(client, parent_id, title, description):
    try:
        return await client.create_child_task(parent_id, title, description)
    finally:
        client.close()


async def _create_branch_then_close(client, repo_path, branch_name):
    try:
        return await client.create_branch(repo_path, branch_name)
    finally:
        client.close()


async def _open_pr_then_close(client, repo_path, branch_name, title, body):
    try:
        return await client.open_pull_request(repo_path, branch_name, title, body)
    finally:
        client.close()


def test_ado_get_work_item_unwraps_structured_content(monkeypatch):
    _patch_to_fake_server(monkeypatch, ado_module, "echo")
    monkeypatch.setenv("FAKE_WRAP_KEY", "workItem")
    client = AdoMcpClient("unused.js", timeout=5)
    wi = asyncio.run(_get_work_item_then_close(client, 404))
    assert wi == {"id": 404}


def test_ado_create_child_task_sends_expected_arguments(monkeypatch):
    _patch_to_fake_server(monkeypatch, ado_module, "echo")
    monkeypatch.setenv("FAKE_WRAP_KEY", "workItem")
    client = AdoMcpClient("unused.js", timeout=5)
    result = asyncio.run(_create_child_task_then_close(client, 404, "Sub A", "desc"))
    assert result == {"parentId": 404, "title": "Sub A", "description": "desc"}


def test_github_create_branch_sends_expected_arguments(monkeypatch):
    _patch_to_fake_server(monkeypatch, github_module, "echo")
    monkeypatch.setenv("FAKE_WRAP_KEY", "branch")
    client = GithubMcpClient("unused.js", timeout=5)
    result = asyncio.run(_create_branch_then_close(client, "/repo", "feature/404-thing"))
    assert result["structuredContent"]["branch"] == {"repoPath": "/repo", "branchName": "feature/404-thing"}


def test_github_open_pull_request_tolerant_of_structured_content_shape(monkeypatch):
    _patch_to_fake_server(monkeypatch, github_module, "echo")
    monkeypatch.setenv("FAKE_WRAP_KEY", "prUrl")
    client = GithubMcpClient("unused.js", timeout=5)
    # Our fake server echoes the arguments back under "prUrl", so the
    # client's tolerant-unwrap logic returns that dict as-is rather
    # than a real URL string -- this just proves the
    # "structuredContent" branch of open_pull_request is taken.
    url = asyncio.run(_open_pr_then_close(client, "/repo", "feature/404-thing", "Title", "Body"))
    assert url == {"repoPath": "/repo", "branchName": "feature/404-thing", "title": "Title", "body": "Body"}
