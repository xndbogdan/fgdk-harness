# REA broker

Small helpers for using [REA](https://github.com/morluto/rea) with the FGDK harness. They keep one `rea mcp` process alive behind a localhost socket, seed Ghidra's analysis from a function census and query the result. They contain no game code, retail data or decompiler output.

## Requirements

- Python 3.11+ (standard library only)
- Node.js 22+
- `rea-agents` (`npm install --global rea-agents`); `npx rea-agents setup` registers its MCP server with your agent if you want to query it directly
- Ghidra, with `GHIDRA_INSTALL_DIR` pointing at it
- Java, with `JAVA_HOME` pointing at it for REA 6.7+

Tested with `rea-agents` 6.7.0, Ghidra 12.1.4 and Java 21 on Windows.

## Seed

REA's default Ghidra analysis misses functions reached only through callback tables. Seed every function start from a census before analysis:

```sh
python tools/rea/rea_seeds.py \
  --census "$OPENV2K/docs/progress/retail-functions.csv" \
  .tmp/v2000-seeds.tsv
```

The CSV needs an `address` column (hex or decimal), such as OpenV2K's public `docs/progress/retail-functions.csv`. For another executable, pass a census you generated. The output is one `0xADDRESS<TAB>function` line per start, LF terminated.

## Run the broker in the background

```sh
python tools/rea/rea_broker.py .tmp/v2000-seeds.tsv
```

Run it in the background and leave it running for the session:

```sh
# POSIX shell
python tools/rea/rea_broker.py .tmp/v2000-seeds.tsv &

# PowerShell
Start-Process -NoNewWindow python `
  -ArgumentList 'tools/rea/rea_broker.py', '.tmp/v2000-seeds.tsv'
```

It prints REA's `initialize` result and then `ready`. The first query imports and analyzes the executable (about 40 seconds); the broker reuses that process, so later queries return in seconds. If you run it in the foreground, your agent waits on a server that never exits.

The seed argument is optional. Without it REA runs unseeded, which still works for most functions but misses callback-table entries. The broker starts `rea mcp` from `PATH`; set `REA_MJS` to the path of `rea-agents/scripts/rea.mjs` to override it. On Windows the npm `rea.cmd` shim is run through `cmd /c`. `REA_BROKER_PORT` selects the port (default `47123`). The child's stderr goes to `<seeds>.stderr.log`, or `rea-broker.stderr.log` when no seed file is given.

## Query

```sh
python tools/rea/reaq.py open_binary \
  '{"path":"C:/Games/V2000/V2000.EXE","provider_id":"ghidra"}'
python tools/rea/reaq.py procedure_pseudo_code '{"procedure":"0x494070"}'
python tools/rea/reaq.py procedure_assembly '{"procedure":"0x494070"}'
python tools/rea/reaq.py procedure_callers '{"procedure":"0x494070"}'
python tools/rea/reaq.py xrefs '{"address":"0x4f7308"}'
python tools/rea/reaq.py read_bytes '{"address":"0x401000","size":64}'
```

Tool names and arguments come from REA; `--raw` prints the full MCP result. Each result starts with its evidence ID.

## Evidence

Evidence IDs live in the broker process. Export the evidence bundle before stopping the broker, with REA's `export_evidence_bundle` tool and a directory under `.tmp/rea-evidence/`. The transcript and bundle are local, uncommitted scratch.

## Limits

- The broker is a thin wrapper over REA's MCP protocol, not a stable API. A REA update can change it; check the broker's stderr log first.
- Ghidra pseudocode is evidence to check against the instructions. Constants can print as function names, register arguments can disappear and stack-slot reads can be hidden. Read the assembly when a detail matters.
- Unseeded analysis misses callback-table functions.
- No game code, retail data or decompiler output is included.

## License

MIT. See [../../LICENSE](../../LICENSE).
