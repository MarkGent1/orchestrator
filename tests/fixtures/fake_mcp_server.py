#!/usr/bin/env python3
"""
Minimal fake JSON-RPC-over-stdio server used to exercise
AdoMcpClient/GithubMcpClient's process- and pipe-handling logic
without depending on a real Node.js MCP server being installed.
Scenario is chosen via argv[1]:

  echo   - reply to every request with structuredContent wrapping the
           request's arguments under the key named by the
           FAKE_WRAP_KEY env var (default "echoed"), so tests can
           exercise the real public API methods (which each unwrap a
           specific key, e.g. result["structuredContent"]["workItem"]).
  noisy  - write a lot of stderr noise before replying normally
           (regression check: a chatty child process must not deadlock
           the parent's stdout reads)
  hang   - read the request but never reply (client must time out)
  crash  - read the first request but exit before replying (simulate
           the server process dying mid-call)
  dead_on_arrival - exit before reading anything at all
"""
import os
import sys
import json


def main():
    scenario = sys.argv[1] if len(sys.argv) > 1 else "echo"

    if scenario == "dead_on_arrival":
        sys.exit(7)

    line = sys.stdin.readline()
    if not line:
        sys.exit(0)

    request = json.loads(line)

    if scenario == "crash":
        sys.exit(3)

    if scenario == "hang":
        # Never write a response; just block so the client's read
        # times out.
        sys.stdin.readline()
        return

    if scenario == "noisy":
        for i in range(2000):
            print(f"noise line {i} " + ("x" * 100), file=sys.stderr, flush=True)

    wrap_key = os.environ.get("FAKE_WRAP_KEY", "echoed")
    response = {
        "jsonrpc": "2.0",
        "id": request["id"],
        "result": {
            "content": [{"type": "text", "text": "ok"}],
            "structuredContent": {wrap_key: request["params"]["arguments"]},
        },
    }
    print(json.dumps(response), flush=True)


if __name__ == "__main__":
    main()
