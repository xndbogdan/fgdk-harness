---
name: fgdk-harness
description: >
  Test and debug the ports of Frontier's FGDK games, V2000 (OpenV2K) and Infestation, against the retail games: run a port headless and repeatable (start states, key replays, fixed steps, snapshots, event logs), reproduce a player's report from their settings, saves and replays, sweep every world for regressions, and test a port feature over real worlds. Use it to check a port change, reproduce a bug report or crash log, or find where a port parts from retail. Pairs with REA for retail-side static analysis.
---

# FGDK harness

V2000 (1998) and Infestation (2000) are Frontier Developments games on one engine, FGDK (I assume Frontier Game Development Kit; Infestation runs its C++ rewrite, Fgdk2). Their ports, OpenV2K and OpenInfestation, run unattended and repeatable from the command line, so each port is its own test harness. Both read the player's own copy of the retail game.

## Paths

Paths differ on every machine. They live in `paths.local.txt` beside this file, one `NAME = path` a line; git ignores it. Before the first command that needs a path, read the file. If the file or the path is missing, ask the user, check that the path exists, and add the line. Ask only for what the task needs. The commands below write the names as shell variables.

| Name | What |
| --- | --- |
| `OPENV2K` | the OpenV2K checkout |
| `V2000_DATA` | retail V2000 for test runs (`PRELOAD.DAT`, `Overlay/`); usually `$OPENV2K/retail` |
| `V2000_INSTALL` | where the user plays V2000 (`settings.json`, `port-config.json`, `SlotNN`) |
| `INFESTATION_PORT` | the OpenInfestation checkout (its Cargo workspace) |
| `INFESTATION_DATA` | a copy of retail Infestation for test runs (`Infest.exe`, `PreLoad.dat`, `Overlay/`) |
| `INFESTATION_INSTALL` | where the user plays Infestation (`port-state/`, `logs/`) |
| `SCRATCH` | a folder for probe runs: settings copies, start states, key replays, output |

## Retail reference (optional)

The probes below show what a port does. To see what retail does, use [REA](https://github.com/morluto/rea): it runs Ghidra over your own copy of a retail executable. The harness includes a small broker in [`tools/rea/`](tools/rea/README.md) that keeps one `rea mcp` process alive. Seed it once, then start it in the background for the session before the first query. Run these commands from this skill's folder: their paths are relative to it. The broker needs no administrator rights.

```sh
# once: write the seed file from a function census
python tools/rea/rea_seeds.py \
  --census "$OPENV2K/docs/progress/retail-functions.csv" .tmp/rea-seeds.tsv

# background, for the session
python tools/rea/rea_broker.py .tmp/rea-seeds.tsv
```

The first query imports and analyzes the executable (about 40 seconds); later queries return in seconds. `reaq.py` queries the running broker. Seeding, requirements and examples are in [`tools/rea/README.md`](tools/rea/README.md). REA is optional: probe, sweep and test runs need only the ports.

For questions REA cannot settle — which branch ran, or how a reconstructed function was actually called — WinDbg or WinDbgX with [Time Travel Debugging](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/time-travel-debugging-overview) (TTD) is the strongest evidence. Record a retail trace into `$SCRATCH` (recording needs WinDbg or `TTD.exe` run as Administrator, so ask the user to start it), then read its call stacks and arguments alongside REA's output; the probes here confirm whether the port matches. Traces contain retail code and must not be committed. TTD is Windows-only and gets tedious once the interesting call paths are known; ordinary testing needs only the harness.

## Rules

- Read the user's install folders, never write into them. Copy settings, saves, logs and replays into `$SCRATCH` first.
- Never capture the desktop: it shows whatever else is open. Use a port's `--snapshot`. Infestation's snapshots keep the framebuffer's alpha (convert to RGB before comparing); OpenV2K's are RGB.
- Retail is the reference. A port change matches retail unless the port's docs say otherwise (Infestation's Vulkan renderers are a remaster). Port fixes are settings, off when comparing with retail.
- No silent approximations: where a port can't know a value retail uses, the feature stops with a logged message, and the report says so.
- Probes are silent (`--hidden`). A run that must be heard needs a visible window at a low volume.
- An exe named with patch, setup, install or update makes Windows ask for admin: rename the copy.
- Downloaded or disc data is untrusted: give it its own folder, and run Python over it with `-I`.
- Never commit diagnostic patches (extra logging, injected values).
- Keep decompiler output and retail code out of the ports' repositories: they take port code and conclusions only.

## Probes

Any probe flag skips the launcher. PowerShell does not wait for these GUI programs: run them from bash or Python, or with `Start-Process -Wait`. A contained stop leaves exit code 0, so read the log, not the exit code.

### OpenV2K

`cargo build --release` in `$OPENV2K`. Its AGENTS.md, "Test runs", lists every flag. To play as the user does, copy `$V2000_INSTALL`'s `settings.json` and `port-config.json` into `$SCRATCH/settings`.

```sh
"$OPENV2K/target/release/v2k-game.exe" --data-dir "$V2000_DATA" --settings "$SCRATCH/settings" \
  --start "$SCRATCH/start.json" --input-replay "$SCRATCH/keys.json" --hidden --renderer software \
  --fixed-step-micros 20000 --frames 1500 --snapshot "$SCRATCH/end.png" \
  --event-log "$SCRATCH/events.jsonl" > "$SCRATCH/out.txt" 2>&1
```

- Without `--settings`, the port reads its registry key `HKCU\Software\V2000 Port\1.0`, which beats `--data-dir`, and a Full Screen setting there switches the monitor's mode.
- A start state's `{"level": N}` takes global overlay ids: 13..48 the campaign, 49 Intro1, 50 Intro2. `{"save": "SlotNN"}` starts from a copy of a save beside the state file.
- Stops: grep stderr for "blocked", "stopped at unresolved data" and "is unowned"; owners' progress lines need `--verbose`.
- Pixel evidence: `--renderer software`. `V2K_SOFTWARE_FRAME_DUMP=DIR` writes every software frame as a BMP. OpenGL runs faster and logs the same.
- A second checkout builds with its own `CARGO_TARGET_DIR` and needs `V2K_RETAIL_DIR` and `V2K_DEMO_DIR`, or the retail tests skip.

### Infestation

`cargo build --release` in `$INFESTATION_PORT`.

```sh
"$INFESTATION_PORT/target/release/inf-game.exe" --no-launcher --data-root "$INFESTATION_DATA" \
  --settings "$SCRATCH/settings.json" --profiles "$SCRATCH/profiles.json" \
  --start "$SCRATCH/start.json" --input-replay "$SCRATCH/keys.json" --renderer opengl --hidden \
  --width 1920 --height 1080 --scaling widescreen --fixed-step-micros 16000 --frames 1500 \
  --snapshot "$SCRATCH/end.png" > "$SCRATCH/out.txt" 2>&1
```

- A start state takes `world`, `start`, `position` `[x, z]`, `heading`, `form` (1 buggy to 5 skimmer), `upgrades`, `known`, `crystals`, `ammo` and more (`crates/inf-game/src/harness_start.rs`). `--write-start-save` turns it into a save.
- `--input-replay` takes SDL key names: Fire Z, Grenade X, Thrust Space, Beam Down D, F12 first person.
- `--fixed-step-micros` takes whole milliseconds, at least 8000.
- `native_words[i]` in `port-state/settings.json` is settings `+4*i`: `+0C` display tier, `+40` full screen, `+60` HUD, `+68` first person, `+70` terrain detail, `+78` pause on hints.
- `--event-log FILE` writes every tick: keep it to short runs (a long replay's reached 38 GB).
- `--session-log DIR` keeps the run and its `.replay`; `--replay-session FILE` reruns one, and with `--resume` plays on live. The game keeps its newest ten replays in `logs/replays` under the data root, and a crash writes `infest-crash-log-<time>.txt` naming the failing owner and its run's replay.
- Stops: grep for "stopped after reached writes", "native world draw failed" and "World view band stopped".

## Sweeps

- OpenV2K: from `$OPENV2K`, `pwsh -NoProfile -File scripts/level-sweep.ps1 -Tag NAME [-Baseline OLD] [-Levels '13..50'] [-Frames 3000]` plays every world from its arrival, hidden at 20 ms steps, into `.tmp/level-sweep/NAME/` (`summary.json`, logs, events, end frames): exit, last state, the frame the player died and notable lines; with `-Baseline`, the lines new (+) or gone (-). All 38 levels at 1500 frames take about 6 minutes.
- Infestation: from `$INFESTATION_PORT`, `python scripts/world_sweep.py --frames 18750 --tag NAME --baseline OLDTAG` plays five game minutes of every world; its docstring has the options and where it writes.

## Port tests

- OpenV2K: retail-backed tests use `#[v2k_test_support::retail_test]` and report as ignored without retail data; `scripts/check.ps1 -RequireRetailData` runs everything.
- Infestation: `crate::test_worlds::offline_world_retained(world, TerrainSpacing::Units256)` loads a real world. A one-off question about a world's data can be a throwaway test.

## From a player's report to a fix

1. Read the report's logs and copy the player's settings, saves and replays into `$SCRATCH`. Infestation: the crash log names the stopped owner and the run's `.replay`; rerun the copy with `--replay-session FILE --data-root "$INFESTATION_DATA" --settings COPY --profiles COPY --hidden` (it writes beside the `.replay`). V2000: copy `settings.json`, `port-config.json` and the save they played, then start from it.
2. Reproduce it at the player's settings (resolution, scaling, detail, renderer), driving with `--input-replay`. If no log line names the cause, log it first.
3. Find what retail does: the port's notes (OpenV2K's `docs/re/`) and its census of retail functions (`docs/progress/retail-functions.csv`) name the code that owns each retail function. The other game's port is a lead, never an answer; OpenV2K's `docs/re/INFESTATION_CROSS_REFERENCE.md` maps what the two share.
4. Fix it in the shared owner, add a test, rerun the probe, then sweep.

## Handing off

Run cargo builds and tests one at a time.

- OpenV2K: work on a branch, run `.\scripts\check.ps1 -RequireRetailData`, and open a pull request to `staging`, as its AGENTS.md says.
- Infestation: `cargo test -p inf-game --no-fail-fast` in `$INFESTATION_PORT`.
