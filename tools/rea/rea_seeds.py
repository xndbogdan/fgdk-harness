"""Write REA's Ghidra seed file from a function census CSV.

    python tools/rea/rea_seeds.py --census PATH OUT.tsv

The CSV needs an `address` column (hex or decimal), such as OpenV2K's public
`docs/progress/retail-functions.csv`. Comment lines starting with `#` are
ignored. The output is one `0xADDRESS<TAB>function` line per start, LF
terminated. REA's parser wants bytes, not text.
"""

import argparse
import csv
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--census", required=True, type=Path, help="function census CSV")
    parser.add_argument("out", type=Path, help="seed TSV to write")
    args = parser.parse_args()

    try:
        source = args.census.open(encoding="utf-8")
    except OSError as error:
        sys.exit(f"cannot read {args.census}: {error}")

    with source:
        rows = csv.DictReader(line for line in source if not line.startswith("#"))
        if rows.fieldnames is None or "address" not in rows.fieldnames:
            sys.exit(f"{args.census} has no 'address' column")
        starts: set[int] = set()
        for row in rows:
            value = (row.get("address") or "").strip()
            if not value:
                continue
            try:
                starts.add(int(value, 0))
            except ValueError:
                try:
                    starts.add(int(value, 16))
                except ValueError:
                    sys.exit(f"bad address in {args.census}: {value!r}")

    if not starts:
        sys.exit(f"no function addresses in {args.census}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    lines = "".join(f"0x{start:08x}\tfunction\n" for start in sorted(starts))
    args.out.write_bytes(lines.encode("ascii"))
    print(f"{len(starts)} seeds -> {args.out}")


if __name__ == "__main__":
    main()
