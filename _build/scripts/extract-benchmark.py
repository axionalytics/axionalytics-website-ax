# -*- coding: utf-8 -*-
"""
AXIONALYTICS — BENCHMARK PROVENANCE EXTRACTOR

Turns a telemetry database into a publishable benchmark block.

WHY THIS EXISTS
---------------
"Under 100ms" is a claim. It is not a benchmark. What makes a number citable is
not the number — it is everything around it: how many samples, over what window,
under what conditions, measured where. A reader can check the second kind and
cannot check the first, and generative engines cite the kind that can be checked.

The site currently publishes timing numbers with none of that. The measurements
themselves already exist in Plowy's telemetry database — this reads them out and
prints the block to paste, so producing provenance is a command rather than a
project.

SCHEMA TOLERANCE
----------------
Column names are not assumed. The script introspects the table, guesses which
column holds latency and which holds the grounding verdict, and tells you what it
picked so you can correct it with --latency-col / --grounding-col. It never
invents a value: a column it cannot find is reported missing, not defaulted.

Usage:
  python _build/scripts/extract-benchmark.py path/to/plowy_telemetry.db
  python _build/scripts/extract-benchmark.py telemetry.db --table turns
  python _build/scripts/extract-benchmark.py telemetry.db --latency-col elapsed_ms
  python _build/scripts/extract-benchmark.py telemetry.db --since 2026-06-01
"""
import io
import json
import os
import sqlite3
import sys

# Ordered by how likely each name is to be the one, so the first hit wins.
LATENCY_HINTS = ["latency_ms", "latency", "elapsed_ms", "duration_ms",
                 "response_ms", "elapsed", "duration", "took_ms"]
GROUNDING_HINTS = ["grounding_passed", "grounding_pass", "grounded",
                   "grounding", "is_grounded", "grounding_ok"]
TIME_HINTS = ["created_at", "timestamp", "ts", "started_at", "asked_at", "time"]
TABLE_HINTS = ["turns", "queries", "requests", "events"]


def die(msg):
    print("\n  %s\n" % msg)
    sys.exit(1)


def pick(columns, hints, override=None, what="column"):
    """First hint present in the table, unless the caller named one."""
    lower = {c.lower(): c for c in columns}
    if override:
        if override.lower() not in lower:
            die("no %s named '%s'. The table has: %s"
                % (what, override, ", ".join(columns)))
        return lower[override.lower()]
    for h in hints:
        if h in lower:
            return lower[h]
    return None


def percentile(sorted_values, p):
    """
    Nearest-rank percentile.

    Deliberately not interpolated: an interpolated p99 is a number that never
    actually happened, and the whole point here is that every figure published
    corresponds to a real observed request.
    """
    if not sorted_values:
        return None
    k = int(round((p / 100.0) * (len(sorted_values) - 1)))
    return sorted_values[max(0, min(k, len(sorted_values) - 1))]


def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("-"):
        print(__doc__)
        return 2

    db_path = args[0]
    if not os.path.exists(db_path):
        die("no such file: %s" % db_path)

    def opt(flag, default=None):
        return args[args.index(flag) + 1] if flag in args else default

    table = opt("--table")
    lat_col = opt("--latency-col")
    gnd_col = opt("--grounding-col")
    since = opt("--since")

    conn = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    tables = [r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    if not tables:
        die("no tables in %s" % db_path)

    if not table:
        table = next((t for t in TABLE_HINTS if t in
                      [x.lower() for x in tables]), None)
        if not table:
            die("could not guess the table. Pass --table with one of: %s"
                % ", ".join(tables))
        table = next(t for t in tables if t.lower() == table)
    elif table not in tables:
        die("no table '%s'. Found: %s" % (table, ", ".join(tables)))

    columns = [r[1] for r in cur.execute(
        "PRAGMA table_info(%s)" % table).fetchall()]

    lat = pick(columns, LATENCY_HINTS, lat_col)
    gnd = pick(columns, GROUNDING_HINTS, gnd_col)
    tcol = pick(columns, TIME_HINTS)

    print("\n  database   %s" % db_path)
    print("  table      %s  (%d columns)" % (table, len(columns)))
    print("  latency    %s" % (lat or "NOT FOUND — pass --latency-col"))
    print("  grounding  %s" % (gnd or "not found (skipping accuracy)"))
    print("  timestamp  %s" % (tcol or "not found (window unknown)"))
    if not lat:
        print("\n  columns available: %s" % ", ".join(columns))
        die("cannot compute latency without a latency column.")

    where = "WHERE %s IS NOT NULL" % lat
    params = []
    if since and tcol:
        where += " AND %s >= ?" % tcol
        params.append(since)

    rows = cur.execute(
        "SELECT %s AS lat%s FROM %s %s ORDER BY %s"
        % (lat, (", %s AS gnd" % gnd) if gnd else "", table, where, lat),
        params).fetchall()

    if not rows:
        die("no rows with a latency value%s."
            % (" since %s" % since if since else ""))

    values = [float(r["lat"]) for r in rows]
    n = len(values)

    window = None
    if tcol:
        w = cur.execute("SELECT MIN(%s) AS a, MAX(%s) AS b FROM %s %s"
                        % (tcol, tcol, table, where), params).fetchone()
        if w and w["a"]:
            window = "%s → %s" % (str(w["a"])[:19], str(w["b"])[:19])

    stats = {
        "n": n,
        "p50_ms": round(percentile(values, 50), 1),
        "p95_ms": round(percentile(values, 95), 1),
        "p99_ms": round(percentile(values, 99), 1),
        "mean_ms": round(sum(values) / n, 1),
        "min_ms": round(values[0], 1),
        "max_ms": round(values[-1], 1),
    }
    if window:
        stats["window"] = window

    if gnd:
        vals = [r["gnd"] for r in rows if r["gnd"] is not None]
        # Accept 1/0, true/false, 'pass'/'fail' — whatever the column holds.
        def truthy(v):
            if isinstance(v, (int, float)):
                return v == 1
            return str(v).strip().lower() in ("1", "true", "t", "yes", "pass",
                                              "passed", "ok")
        if vals:
            passed = sum(1 for v in vals if truthy(v))
            stats["grounding_evaluated"] = len(vals)
            stats["grounding_passed"] = passed
            stats["grounding_pass_rate"] = round(passed / float(len(vals)), 4)

    print("\n  ── measured ──────────────────────────────────────────────")
    print("     n          %s" % f"{n:,}")
    if window:
        print("     window     %s" % window)
    print("     p50        %.1f ms" % stats["p50_ms"])
    print("     p95        %.1f ms" % stats["p95_ms"])
    print("     p99        %.1f ms" % stats["p99_ms"])
    print("     mean       %.1f ms" % stats["mean_ms"])
    print("     range      %.1f – %.1f ms" % (stats["min_ms"], stats["max_ms"]))
    if "grounding_pass_rate" in stats:
        print("     grounding  %.1f%%  (%d of %d)"
              % (stats["grounding_pass_rate"] * 100,
                 stats["grounding_passed"], stats["grounding_evaluated"]))

    # The three fields the site generator will require before it renders a
    # number: without them this is a claim wearing a lab coat.
    print("\n  ── still needed from you (the script cannot know these) ──")
    print("     hardware   what it ran on")
    print("     conditions warm/cold cache, load, which deployment")
    print("     excludes   what the timer does NOT cover (network? queueing?)")

    stats.update({"hardware": "TODO", "conditions": "TODO", "excludes": "TODO"})

    out = os.path.join(os.path.dirname(os.path.abspath(db_path)),
                       "benchmark-extract.json")
    with io.open(out, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(stats, indent=2))
    print("\n  wrote %s — fill the three TODOs, then it is publishable.\n" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
