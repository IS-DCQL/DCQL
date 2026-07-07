#!/usr/bin/env python3
"""Step 3 -- run + time the T2 / T3 MQL queries (server-side, explain executionStats).

Key point: the query TEXT is NOT hardcoded here. Each query is read from the §6.2
conciseness folder and executed against pymongo, so the performance run and the published
query listings stay in sync:

    ../../conciseness/MQL/biomedical/T2.js        db.cases.find(...)
    ../../conciseness/MQL/biomedical/T3.js        db.cases.aggregate([...])
    ../../conciseness/MQL/organic-polymer/T2.js   db.processing_logs.find(...)
    ../../conciseness/MQL/organic-polymer/T3.js   db.materials_library.aggregate([...])

Each .js file is a mongosh statement (db.<coll>.find(...) / db.<coll>.aggregate([...])).
This script parses out the collection + filter/projection/pipeline, then times it with the
SAME method as the original time.py: db.command("explain", {find|aggregate ...},
verbosity="executionStats") -> executionStats.executionTimeMillis. That measures pure
MongoDB server-side execution time (no client fetch cost).

Connection / behaviour via env vars:
    MONGO_URI   (default mongodb://localhost:27017)
    BIO_DB      biomedical database name      (default dcql_bio)
    POLY_DB     organic-polymer database name (default dcql_poly)
    RUNS, WARMUP, TRIM_RATIO   (defaults 100 / 1 / 0.2)
"""
import json
import math
import os
import re

from pymongo import MongoClient

HERE = os.path.dirname(os.path.abspath(__file__))

# ========== CONFIG (override via env) ==========
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
BIO_DB = os.environ.get("BIO_DB", "dcql_bio")
POLY_DB = os.environ.get("POLY_DB", "dcql_poly")

# Query text is sourced from the conciseness folder.
QUERY_ROOT = os.environ.get(
    "MQL_QUERY_ROOT",
    os.path.join(HERE, "..", "..", "conciseness", "MQL"),
)

RUNS = int(os.environ.get("RUNS", "100"))
WARMUP = int(os.environ.get("WARMUP", "1"))
TRIM_RATIO = float(os.environ.get("TRIM_RATIO", "0.2"))
PRINT_EACH_RUN = os.environ.get("PRINT_EACH_RUN", "0") == "1"
# ===============================================

# Which query files to benchmark, and which db each runs against.
QUERIES = [
    {"name": "biomedical/T2 (find by case_id)", "db": BIO_DB, "file": "biomedical/T2.js"},
    {"name": "biomedical/T3 (aggregate RNA primary tumor)", "db": BIO_DB, "file": "biomedical/T3.js"},
    {"name": "organic-polymer/T2 (find processing_logs)", "db": POLY_DB, "file": "organic-polymer/T2.js"},
    {"name": "organic-polymer/T3 (aggregate materials_library + lookup)", "db": POLY_DB, "file": "organic-polymer/T3.js"},
]


# ---------------------------------------------------------------------------
# Parse a mongosh .js statement into (collection, op, args) and run via explain.
# ---------------------------------------------------------------------------
def _strip_comments(text):
    # remove // line comments and /* */ block comments
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//[^\n]*", "", text)
    return text


def _split_top_level_args(s):
    """Split the top-level comma-separated arguments of a call's (...) body."""
    args, depth, start, in_str, quote = [], 0, 0, False, ""
    for i, ch in enumerate(s):
        if in_str:
            if ch == quote and s[i - 1] != "\\":
                in_str = False
            continue
        if ch in "\"'":
            in_str, quote = True, ch
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "," and depth == 0:
            args.append(s[start:i])
            start = i + 1
    tail = s[start:]
    if tail.strip():
        args.append(tail)
    return args


def _js_to_json(expr):
    """Best-effort convert a Mongo JS object/array literal to a Python value.

    Handles: unquoted keys ($-prefixed and bare), single quotes, trailing commas.
    The query files use only plain literals (numbers, strings, $-operators), so this is
    sufficient and keeps the published query text as the single source of truth.
    """
    s = expr.strip()
    if not s:
        return {}
    # single -> double quotes (no escaped single quotes appear in the query files)
    s = re.sub(r"'([^']*)'", r'"\1"', s)
    # quote unquoted object keys, including $operators: { $gt: 1 } / { foo: 1 }
    s = re.sub(r'([{,]\s*)([$A-Za-z_][\w$.]*)\s*:', r'\1"\2":', s)
    # remove trailing commas before } or ]
    s = re.sub(r",(\s*[}\]])", r"\1", s)
    return json.loads(s)


CALL_RE = re.compile(r"db\.(\w+)\.(find|aggregate)\s*\((.*)\)\s*;?\s*$", re.S)


def parse_query_file(path):
    """Return (collection, op, payload) where payload is the explain command body
    (minus the leading find/aggregate verb)."""
    raw = _strip_comments(open(path, encoding="utf-8").read()).strip()
    m = CALL_RE.search(raw)
    if not m:
        raise ValueError(f"Could not parse a db.<coll>.find/aggregate(...) call in {path}")
    coll, op, body = m.group(1), m.group(2), m.group(3).strip()

    if op == "find":
        args = _split_top_level_args(body)
        filt = _js_to_json(args[0]) if args else {}
        cmd = {"find": coll, "filter": filt}
        if len(args) >= 2 and args[1].strip():
            cmd["projection"] = _js_to_json(args[1])
        return coll, op, cmd

    # aggregate -- body is a single array literal (the pipeline)
    pipeline = _js_to_json(body)
    return coll, op, {"aggregate": coll, "pipeline": pipeline, "cursor": {}}


def _extract_exec_time(explain_result):
    stats = explain_result.get("executionStats", {})
    if "executionTimeMillis" in stats:
        return stats["executionTimeMillis"]
    # aggregate explain may nest stats inside a $cursor stage
    for stage in explain_result.get("stages", []):
        cur = stage.get("$cursor")
        if cur and "executionTimeMillis" in cur.get("executionStats", {}):
            return cur["executionStats"]["executionTimeMillis"]
    raise KeyError("executionTimeMillis not found in explain result")


def get_execution_time_ms(db, command):
    """Run explain('executionStats') on a find/aggregate command body (same as time.py)."""
    explain_result = db.command("explain", command, verbosity="executionStats")
    return _extract_exec_time(explain_result)


# ---------------------------------------------------------------------------
# Trimmed statistics + benchmark loop (carried over from time.py).
# ---------------------------------------------------------------------------
def calc_trimmed_stats(values, trim_ratio=0.2):
    if not values:
        raise ValueError("no values to summarize")
    sorted_values = sorted(values)
    n = len(sorted_values)
    trim_count = int(n * trim_ratio)
    if n - 2 * trim_count <= 0:
        trimmed, trim_count = sorted_values, 0
    else:
        trimmed = sorted_values[trim_count:n - trim_count]
    used_n = len(trimmed)
    avg = sum(trimmed) / used_n
    if used_n >= 2:
        var = sum((x - avg) ** 2 for x in trimmed) / (used_n - 1)
        stddev = math.sqrt(var)
    else:
        stddev = 0.0
    return {
        "raw_runs": n, "used_runs": used_n, "trim_count_each_side": trim_count,
        "sorted_times": sorted_values, "trimmed_times": trimmed,
        "avg": avg, "min": min(trimmed), "max": max(trimmed), "sample_stddev": stddev,
        "raw_min": min(sorted_values), "raw_max": max(sorted_values),
    }


def benchmark(name, time_func):
    print(f"\n===== Benchmark: {name} =====")
    print(f"Warmup runs: {WARMUP} | Measured runs: {RUNS} | Trim: each side {TRIM_RATIO*100:.0f}%")
    print("-" * 60)
    for i in range(WARMUP):
        print(f"Warmup {i+1}: {time_func()} ms")
    times = []
    for i in range(RUNS):
        t = time_func()
        times.append(t)
        if PRINT_EACH_RUN:
            print(f"Run {i+1}: {t} ms")
    stats = calc_trimmed_stats(times, TRIM_RATIO)
    print("\n----- Summary -----")
    print(f"Query: {name}")
    print(f"Raw runs: {stats['raw_runs']} | Used after trim: {stats['used_runs']} "
          f"(trim {stats['trim_count_each_side']} each side)")
    print(f"Raw range: {stats['raw_min']} .. {stats['raw_max']} ms")
    print(f"Average (trimmed): {stats['avg']:.2f} ms")
    print(f"Min/Max (trimmed): {stats['min']} / {stats['max']} ms")
    print(f"Sample StdDev (trimmed): {stats['sample_stddev']:.2f} ms")
    return times, stats


def main():
    client = MongoClient(MONGO_URI)
    print(f"MongoDB URI: {MONGO_URI}")
    print(f"Query source: {os.path.abspath(QUERY_ROOT)}")
    print("Timing source: explain('executionStats').executionTimeMillis "
          "(server-side execution time only)")
    print(f"Measured runs per query: {RUNS}")
    try:
        for q in QUERIES:
            path = os.path.join(QUERY_ROOT, q["file"])
            if not os.path.exists(path):
                print(f"\n[skip] {q['name']} -- query file not found: {path}")
                continue
            coll, op, command = parse_query_file(path)
            db = client[q["db"]]
            print(f"\n# {q['name']}")
            print(f"  source : {os.path.relpath(path, HERE)}")
            print(f"  target : {q['db']}.{coll} ({op})")
            benchmark(q["name"], lambda db=db, cmd=command: get_execution_time_ms(db, cmd))
    finally:
        client.close()


if __name__ == "__main__":
    main()
