"""A persistent, seeded `rea mcp` behind a localhost line-JSON socket.

    python tools/rea/rea_broker.py [SEEDS.tsv]

Run it in the background and leave it running for the session. The first query
imports and analyzes the executable (about 40 seconds); later queries return in
seconds. Query it with `reaq.py`.

The broker starts `rea mcp` from PATH. `REA_MJS` overrides it with the path to
`rea-agents/scripts/rea.mjs` (then it runs through `node`). `REA_BROKER_PORT`
selects the port (default 47123). The child's stderr goes to
`<SEEDS>.stderr.log`, or `rea-broker.stderr.log` when no seed file is given.

See README.md.
"""

import itertools
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
from pathlib import Path

PORT = int(os.environ.get("REA_BROKER_PORT", "47123"))


def rea_command() -> list[str]:
    mjs = os.environ.get("REA_MJS")
    if mjs:
        return ["node", mjs, "mcp"]
    exe = shutil.which("rea")
    if not exe:
        raise SystemExit(
            "rea was not found on PATH. Install it with "
            "`npm install --global rea-agents`, or set REA_MJS to "
            "rea-agents/scripts/rea.mjs."
        )
    if os.name == "nt" and Path(exe).suffix.lower() in {".cmd", ".bat"}:
        return ["cmd", "/c", exe, "mcp"]
    return [exe, "mcp"]


def main() -> None:
    if len(sys.argv) > 2:
        sys.exit(__doc__)
    seeds = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else None
    if seeds is not None and not seeds.is_file():
        sys.exit(f"seed file not found: {seeds}")
    log_path = Path(f"{seeds}.stderr.log") if seeds else Path("rea-broker.stderr.log")
    env = dict(os.environ)
    if seeds is not None:
        env["REA_GHIDRA_SEED_FILE"] = str(seeds)

    command = rea_command()
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    with log_path.open("wb") as log:
        try:
            proc = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=log,
                env=env,
                creationflags=creationflags,
            )
        except FileNotFoundError as error:
            sys.exit(
                f"cannot start REA: {error}. Install Node.js and rea-agents, "
                "or set REA_MJS."
            )

        ids = itertools.count(1)
        lock = threading.Lock()

        def rpc(method: str, params: dict | None = None, notify: bool = False):
            message = {"jsonrpc": "2.0", "method": method}
            if params is not None:
                message["params"] = params
            if not notify:
                message["id"] = next(ids)
            try:
                proc.stdin.write((json.dumps(message) + "\n").encode())
                proc.stdin.flush()
            except (BrokenPipeError, OSError):
                raise SystemExit(f"rea mcp exited; see {log_path}")
            if notify:
                return None
            while True:
                line = proc.stdout.readline()
                if not line:
                    raise SystemExit(f"rea mcp exited; see {log_path}")
                try:
                    reply = json.loads(line)
                except ValueError:
                    continue
                if reply.get("id") == message["id"]:
                    return reply

        try:
            greeting = rpc(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "reaq", "version": "1"},
                },
            )
            print(json.dumps(greeting)[:300], flush=True)
            rpc("notifications/initialized", notify=True)

            server = socket.socket()
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                server.bind(("127.0.0.1", PORT))
            except OSError as error:
                raise SystemExit(
                    f"cannot bind 127.0.0.1:{PORT}: {error}. "
                    "Set REA_BROKER_PORT to a free port."
                )
            server.listen(4)
            print("ready", flush=True)
            while True:
                client, _ = server.accept()
                with client:
                    stream = client.makefile("rwb")
                    try:
                        request = json.loads(stream.readline())
                        tool = request["tool"]
                    except (ValueError, KeyError, TypeError) as error:
                        # A client that closes early or sends no request must not
                        # end the broker.
                        reply = {"error": f"bad request: {error}"}
                    else:
                        with lock:
                            reply = rpc(
                                "tools/call",
                                {"name": tool, "arguments": request.get("args", {})},
                            )
                    try:
                        stream.write((json.dumps(reply) + "\n").encode())
                        stream.flush()
                    except OSError:
                        pass
        except KeyboardInterrupt:
            pass
        finally:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=creationflags,
                )
            else:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()


if __name__ == "__main__":
    main()
