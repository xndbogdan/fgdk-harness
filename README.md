# FGDK harness

An agent skill for testing and debugging the ports of Frontier's FGDK games: [OpenV2K](https://github.com/xndbogdan/OpenV2K) (V2000, 1998) and the Infestation port (Infestation, 2000). It teaches a coding agent to run either port headless and repeatable, reproduce a player's bug report, sweep every world for regressions and test port features over real worlds.

I use it for my own work on OpenV2K and the Infestation port. OpenV2K is public; the Infestation port is not yet public.

The harness is meant to be used with [REA](https://github.com/morluto/rea). The port commands answer "what does the port do?"; REA runs Ghidra over your own copy of the retail executables and answers "what does retail do here?". That comparison is the point. REA is optional: the probes, sweeps and port tests work without it.

You need your own copy of the retail games. This repository contains no game code, retail data or decompiler output.

## FGDK

I assume FGDK stands for **Frontier Game Development Kit**. Neither the retail executables nor Frontier's later Cobra archive names spell it out.

The name survives in the original build paths. V2000's engine lives under `C:\Coding\FGDK\`, Infestation's under `C:\Coding\Fgdk2\`:

```text
C:\Coding\FGDK\Code\Windows\     V2000's engine (C)
C:\Coding\virus2\code\common\    V2000's game
C:\Coding\Fgdk2\Code\Windows\    Infestation's engine (C++)
C:\Coding\V3000\Code\Common\     Infestation's game
```

V2000's game folder is `virus2`, not `V2000`. I can only speculate that, internally, Infestation was considered a successor to V2000, judging by the name (`virus2` to `V3000`, `FGDK` to `Fgdk2`); the code evidence is separate.

See [FGDK.md](FGDK.md) for the strings, offsets and reference counts.

## Install

Clone it into your agent's skills folder. For Claude Code:

```sh
git clone https://github.com/xndbogdan/fgdk-harness ~/.claude/skills/fgdk-harness
```

For another agent, copy the folder into its skills directory; keep `SKILL.md`, `README.md`, `FGDK.md` and `tools/` together.

## Paths

The first time the skill needs a path (your OpenV2K checkout, your retail data, where you play), it asks and writes the answer to `paths.local.txt` beside `SKILL.md`, which git ignores. To set them ahead, create that file yourself, one `NAME = path` a line, with the names `SKILL.md` lists:

```text
OPENV2K = C:\src\OpenV2K
V2000_DATA = C:\src\OpenV2K\retail
SCRATCH = C:\scratch\fgdk
```

An Infestation run also needs `INFESTATION_PORT`, `INFESTATION_DATA` and `INFESTATION_INSTALL`; `SKILL.md` describes each one.

## REA

Install REA and register its MCP server as [its README](https://github.com/morluto/rea) describes:

```sh
npm install --global rea-agents
npx rea-agents setup
```

REA needs Node.js 22.19+, 24.11+ or 26+, Ghidra and Java. The broker scripts in [`tools/rea/`](tools/rea/README.md) need Python 3.11+ and no third-party packages. The broker is only a persistent wrapper; REA's own MCP server also works directly.

For repeated queries, run the broker in the background and leave it running for the session. It keeps one `rea mcp` process alive: the first query imports and analyzes the executable (about 40 seconds), and later queries return in seconds. It needs no administrator rights: it listens on 127.0.0.1, and REA keeps its Ghidra project in the temp folder. Two things do need an elevated terminal on Windows: `npm install --global` when npm's global folder is under Program Files (`npm root -g` shows it), and recording TTD traces.

```sh
# once: write a seed file from a function census
python tools/rea/rea_seeds.py \
  --census "$OPENV2K/docs/progress/retail-functions.csv" \
  .tmp/v2000-seeds.tsv

# background, for the session
python tools/rea/rea_broker.py .tmp/v2000-seeds.tsv

# another shell: query the running broker
python tools/rea/reaq.py open_binary \
  '{"path":"C:/Games/V2000/V2000.EXE","provider_id":"ghidra"}'
python tools/rea/reaq.py procedure_pseudo_code '{"procedure":"0x494070"}'
```

Run the broker in the background (a second terminal, your shell's background operator, or `Start-Process`), and leave it running while you query. It listens on `127.0.0.1:47123` by default; set `REA_BROKER_PORT` to move it. `REA_MJS` overrides the `rea` entry script. The seed file is optional; unseeded analysis still works, but functions reached only through callback tables may answer "No procedure exists". See [`tools/rea/README.md`](tools/rea/README.md) for requirements, seeding another executable and the evidence caveats.

## TTD traces

For the harder questions — which branch retail took, or how a function REA reconstructed was actually called — use WinDbg or WinDbgX with [Time Travel Debugging](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/time-travel-debugging-overview) (TTD) heavily while you are still mapping the code. Record a trace of the retail game, then use it to look up the call stacks, arguments and execution paths. That gave me the most solid evidence base for the agent, and TTD plus this harness is how I check that a reimplementation conforms to retail.

Recording needs WinDbg or `TTD.exe` run as Administrator. TTD traces are large and contain retail code and data: keep them in your scratch folder and never commit them. TTD is Windows-only and gets tedious once the interesting call paths are understood. After that, the harness alone is enough for ordinary testing.

## Background

The project started as a solo effort to extract assets from these games. It became a personal fascination with how they work, then a reverse-engineering effort on V2000 and Infestation, where retail accuracy mattered more to me than anything else. I didn't just want to throw a slop grenade on the internet, call it a day and pat myself on the back. As coding agents improved, I used every model I could get my hands on, and the harness grew out of the workflow that kept them honest against retail. It began as a section in my `AGENTS.md`; it outgrew that file, so I made it a skill of its own.

## License

MIT. See [LICENSE](LICENSE).
