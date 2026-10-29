# FGDK and the original build paths

FGDK is the name Frontier Developments used for the engine shared by V2000 (1998) and Infestation (2000). I assume it stands for **Frontier Game Development Kit**. Neither the retail executables nor Frontier's later Cobra archive names spell the letters out, so that expansion is an assumption, not a recovered fact.

## Where the name appears

I know of two places:

1. **Source paths in the retail executables.** Both games still carry the `__FILE__` strings their error reports print, under `C:\Coding\FGDK\...` in V2000 and `C:\Coding\Fgdk2\...` in Infestation.
2. **Archive type names in Frontier's later Cobra engine.** In [OpenNaja/cobra-tools](https://github.com/OpenNaja/cobra-tools), each game's `constants/<game>/mimes.py` lists types such as `FGDK:Text:txt`, `FGDK:Texture`, `FGDK:LuaModule` and `FGDK:model2`. The games include Zoo Tycoon, Planet Coaster and Planet Coaster 2, Jurassic World Evolution 1, 2 and 3, Planet Zoo, Disneyland Adventures, and Warhammer Age of Sigmar: Realms of Ruin.

## Engine source paths

All six strings are in the `.data` section. The offsets are for these copies:

- `V2000.EXE`: SHA-256 `e9be7a83…b4ba`, the September 1998 pressing.
- `Infest.exe`: SHA-256 `bf09f66e…4956`.

| Exe | String | File offset | Address | References in code |
| --- | --- | --- | --- | ---: |
| `V2000.EXE` | `C:\Coding\FGDK\Code\Windows\Graph2D.c` | `0xD4520` | `0x004D5D20` | 306 |
| `V2000.EXE` | `C:\Coding\FGDK\Code\Windows\movie.c` | `0xD4668` | `0x004D5E68` | 6 |
| `V2000.EXE` | `C:\Coding\FGDK\Code\Windows\DDCalls.c` | `0xD4D98` | `0x004D6598` | 117 |
| `Infest.exe` | `C:\Coding\Fgdk2\Code\Windows\movie.cpp` | `0x140D70` | `0x00540D70` | 11 |
| `Infest.exe` | `C:\Coding\Fgdk2\Code\Windows\Graph2D.cpp` | `0x144710` | `0x00544710` | 167 |
| `Infest.exe` | `C:\Coding\Fgdk2\Code\Windows\DDCalls.cpp` | `0x145408` | `0x00545408` | 95 |

Anyone can find the strings again with `strings V2000.EXE | grep -i fgdk`.

## Game source paths

The game code sits beside the engine, but V2000's folder is `virus2`, not `V2000`, and Infestation's is `V3000`:

| Exe | String | File offset | Address | References in code |
| --- | --- | --- | --- | ---: |
| `V2000.EXE` | `c:\Coding\virus2\code\common\objtable.c` | `0xC98C8` | `0x004CB0C8` | 9 |
| `Infest.exe` | `C:\Coding\V3000\Code\Common\Objtable.cpp` | `0x138A88` | `0x00538A88` | 9 |

Both strings sit in `.data`, in the same copies as above.

Each is the file name the object-table code reports when it fails. Every routine there that can fail passes this name and a line number to `"FATAL ERROR: File %s Line %d"`:

- V2000: `0043A0C0`, `0043A290`, `0043A3C0`, `0043A6E0`;
- Infestation: `00461CE0`, `00461EA0`, `00461FE0`, `004622F0`.

The line numbers match almost one for one between the two files, which is part of the evidence that Infestation continues V2000's code.

## The build tree

```text
C:\Coding\FGDK\Code\Windows\     V2000's engine (C)
C:\Coding\virus2\code\common\    V2000's game
C:\Coding\Fgdk2\Code\Windows\    Infestation's engine (C++)
C:\Coding\V3000\Code\Common\     Infestation's game
```

That is every build path in the two executables:

- Neither exe has a debug directory, so there is no `.pdb` path.
- Other drive paths are not build folders. V2000 has its LaserLok copy-protection and debug files (`x:\LASERLOK\LASERLOK.IN`, `C:\DEBUG.SP` and similar). Infestation has its default install folder `C:\Program Files\Infestation\` and `c:\bad_lode.txt`.

The names suggest Infestation was internally treated as V2000's successor: `virus2` became `V3000`, and `FGDK` became `Fgdk2`. That is speculation from the names; the code evidence is separate. The object-table line numbers above match almost one for one, and the two games share large parts of the engine's platform layer.

Build dates, from the executables: V2000 was linked 1998-09-16; Infestation 2000-07-14.

## Limits

I checked only the two executables above. I did not check the November 1998 V2000 pressing or the PlayStation discs; their builds may carry different paths.
