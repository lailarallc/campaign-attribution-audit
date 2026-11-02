"""Split the event export into one download per month (Cloudflare Pages caps files at 25 MB).
Concatenating the three files' rows (one header) reproduces data/export/events.csv.gz exactly.
Output: static/data/events_2026-07.csv.gz, _08, _09, static/data/spend.csv and the three
data/truth/*.csv.gz files copied as static/data/truth_*.csv.gz.
"""

import gzip
import io
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "static" / "data"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with gzip.open(ROOT / "data" / "export" / "events.csv.gz", "rt", encoding="utf-8", newline="") as f:
        header = f.readline()
        parts = {}
        for line in f:
            month = line[:6]   # event_date is the first column, YYYYMMDD
            parts.setdefault(month, io.StringIO()).write(line)
    for month, buf in sorted(parts.items()):
        name = OUT / f"events_{month[:4]}-{month[4:]}.csv.gz"
        with open(name, "wb") as fh, gzip.GzipFile(filename="", mode="wb", fileobj=fh, mtime=0) as gz:
            gz.write((header + buf.getvalue()).encode("utf-8"))
        print(f"wrote {name.name} ({name.stat().st_size / 1e6:.1f} MB)")
    shutil.copy(ROOT / "data" / "spend.csv", OUT / "spend.csv")
    for name in ("seed_log.csv.gz", "sessions.csv.gz", "orders.csv.gz"):   # what the hygiene ledger reads
        shutil.copy(ROOT / "data" / "truth" / name, OUT / ("truth_" + name))


if __name__ == "__main__":
    main()
