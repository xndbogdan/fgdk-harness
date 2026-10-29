"""Call the seeded REA broker (rea_broker.py) and print the result value.

    python tools/rea/reaq.py TOOL 'JSON-ARGS' [--raw]
    python tools/rea/reaq.py procedure_pseudo_code '{"procedure":"0x494070"}'

Start the broker in the background first; see README.md. Each result prints its
Evidence ID first (`# ev_...`).
"""

import json
import os
import socket
import sys


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    port = int(os.environ.get("REA_BROKER_PORT", "47123"))
    try:
        stream = socket.create_connection(("127.0.0.1", port)).makefile("rwb")
    except OSError as error:
        sys.exit(
            f"cannot reach the REA broker on 127.0.0.1:{port}: {error}\n"
            "Start it in the background first: "
            "python tools/rea/rea_broker.py [SEEDS.tsv]"
        )

    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] != "--raw" else {}
    stream.write((json.dumps({"tool": sys.argv[1], "args": args}) + "\n").encode())
    stream.flush()
    line = stream.readline()
    try:
        reply = json.loads(line)
    except ValueError:
        sys.exit(f"bad reply from the REA broker: {line!r}")
    if "--raw" in sys.argv:
        print(json.dumps(reply, indent=1))
        sys.exit()
    if "error" in reply:
        print("ERROR", json.dumps(reply["error"]))
        sys.exit(1)
    for part in reply["result"].get("content", []):
        if part.get("type") != "text":
            continue
        try:
            result = json.loads(part["text"])
        except ValueError:
            print(part["text"])
            continue
        value = result.get("raw_result", result.get("result", result))
        if isinstance(value, dict) and "value" in value:
            value = value["value"]
        print("#", result.get("evidence_id", ""))
        print(value if isinstance(value, str) else json.dumps(value, indent=1))


if __name__ == "__main__":
    main()
