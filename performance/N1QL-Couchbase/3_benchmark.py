#!/usr/bin/env python3
"""Step 3 -- run + time the T2 / T3 N1QL queries (server-side execution time).

Key point: the query TEXT is NOT hardcoded here. Each query is read from the §6.2
conciseness folder and executed via the Couchbase SDK, so the performance run and the
published query listings stay in sync:

    ../../conciseness/N1QL/biomedical/T2.n1ql       SELECT ... FROM cases ... case_id = ...
    ../../conciseness/N1QL/biomedical/T3.n1ql       SELECT DISTINCT case_id ... (RNA primary tumor)
    ../../conciseness/N1QL/organic-polymer/T2.n1ql  SELECT ... FROM processing_logs ...
    ../../conciseness/N1QL/organic-polymer/T3.n1ql  SELECT ... materials_library JOIN processing_logs

Each .n1ql file is plain N1QL text. This script reads it, points the FROM keyspace at the
bucket actually loaded by 2_load.py (the published files mix `medical` / `dcql` bucket names;
they are normalised to CB_BUCKET here while preserving the rest of the query verbatim), then
times it with the SAME method as the original time_*.py: cluster.query(..., metrics=True,
profile="timings") and read metadata().metrics().execution_time() -- the pure server-side
N1QL execution time (no client fetch cost). Trimmed-mean stats carried over from time_*.py.

Connection / behaviour via env vars (defaults shown):
    CB_CONN_STR        couchbase://127.0.0.1
    CB_USERNAME        admin
    COUCHBASE_PASSWORD (no default -- must be set)
    CB_BUCKET          dcql
    CB_SCOPE           _default
    RUNS=50  WARMUP=1  TRIM_FAST_RATIO=0.2  TRIM_SLOW_RATIO=0.2  SLEEP_SECONDS=2
    N1QL_QUERY_ROOT    (defaults to ../../conciseness/N1QL)
    PRINT_EACH_RUN=0
"""
import os
import re
import statistics
import time
from datetime import datetime, timedelta

from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions, QueryOptions

HERE = os.path.dirname(os.path.abspath(__file__))

# ========== CONFIG (override via env) ==========
CONN_STR = os.environ.get("CB_CONN_STR", "couchbase://127.0.0.1")
USERNAME = os.environ.get("CB_USERNAME", "admin")
PASSWORD = os.environ.get("COUCHBASE_PASSWORD", "")

BUCKET_NAME = os.environ.get("CB_BUCKET", "dcql")
SCOPE_NAME = os.environ.get("CB_SCOPE", "_default")

QUERY_ROOT = os.environ.get(
    "N1QL_QUERY_ROOT",
    os.path.join(HERE, "..", "..", "conciseness", "N1QL"),
)

RUNS = int(os.environ.get("RUNS", "50"))
WARMUP = int(os.environ.get("WARMUP", "1"))
SLEEP_SECONDS = float(os.environ.get("SLEEP_SECONDS", "2"))
TIMEOUT_SECONDS = int(os.environ.get("TIMEOUT_SECONDS", "500"))
TRIM_FAST_RATIO = float(os.environ.get("TRIM_FAST_RATIO", "0.2"))
TRIM_SLOW_RATIO = float(os.environ.get("TRIM_SLOW_RATIO", "0.2"))
PRINT_EACH_RUN = os.environ.get("PRINT_EACH_RUN", "0") == "1"
# ===============================================

QUERIES = [
    {"name": "biomedical/T2 (find by case_id on cases)", "file": "biomedical/T2.n1ql"},
    {"name": "biomedical/T3 (RNA / primary-tumor on cases)", "file": "biomedical/T3.n1ql"},
    {"name": "organic-polymer/T2 (find on processing_logs)", "file": "organic-polymer/T2.n1ql"},
    {"name": "organic-polymer/T3 (materials_library JOIN processing_logs)",
     "file": "organic-polymer/T3.n1ql"},
]

# Bucket names that appear in the published query files; all are normalised to CB_BUCKET so
# the queries run against the single bucket loaded by 2_load.py.
KNOWN_BUCKETS = ["medical", "dcql"]

# The biomedical queries are written against the bucket's default keyspace (e.g. `FROM
# medical c` / `FROM dcql c`), whereas 2_load.py imports the merged patient docs into a named
# `cases` collection. Map that bare bucket reference to the explicit cases keyspace so the
# published query runs unchanged otherwise. The polymer queries are already fully qualified
# (`bucket._default.collection`) and only need the bucket name rewritten.
BIO_COLLECTION = os.environ.get("BIO_COLLECTION", "cases")


def normalize_bucket(sql):
    """Rewrite the keyspace in the published query to match what 2_load.py loaded."""
    for b in KNOWN_BUCKETS:
        # backticked bucket immediately followed by scope/collection -> just rename bucket
        sql = re.sub(rf"`{b}`(\s*\.\s*[`_\w])", rf"`{BUCKET_NAME}`\1", sql)
        # bare bucket immediately followed by scope/collection -> rename bucket
        sql = re.sub(rf"(?<![\w.`]){b}(\s*\.\s*[`_\w])", rf"{BUCKET_NAME}\1", sql)
        # bare/backticked bucket as a *default-keyspace* reference (no scope.collection after)
        # -> expand to the explicit cases collection
        sql = re.sub(
            rf"(\b(?:FROM|JOIN)\s+)`?{b}`?(\s+|$)",
            rf"\g<1>`{BUCKET_NAME}`.`{SCOPE_NAME}`.`{BIO_COLLECTION}`\2",
            sql, flags=re.I,
        )
    return sql


def load_query(path):
    sql = open(path, encoding="utf-8").read().strip()
    if sql.endswith(";"):
        sql = sql[:-1]
    return normalize_bucket(sql)


# ===== trimmed stats (carried over from time_*.py) =====
def percentile(data, p):
    if not data:
        return None
    s = sorted(data)
    k = (len(s) - 1) * (p / 100)
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[int(k)]
    return s[f] + (s[c] - s[f]) * (k - f)


def calc_trimmed_stats(data, trim_fast_ratio=0.2, trim_slow_ratio=0.2):
    if not data:
        return None
    sorted_data = sorted(data)
    n = len(sorted_data)
    fast_cut = int(n * trim_fast_ratio)
    slow_cut = int(n * trim_slow_ratio)
    trimmed = sorted_data[fast_cut:(n - slow_cut) if slow_cut > 0 else n]
    if not trimmed:
        trimmed, fast_cut, slow_cut = sorted_data, 0, 0
    avg = statistics.mean(trimmed)
    stddev = statistics.stdev(trimmed) if len(trimmed) >= 2 else 0.0
    return {
        "raw_count": len(data), "sorted_data": sorted_data,
        "trim_fast_count": fast_cut, "trim_slow_count": slow_cut, "used_count": len(trimmed),
        "raw_min": min(sorted_data), "raw_max": max(sorted_data),
        "raw_avg": statistics.mean(sorted_data), "raw_median": statistics.median(sorted_data),
        "raw_p90": percentile(sorted_data, 90), "raw_p95": percentile(sorted_data, 95),
        "raw_p99": percentile(sorted_data, 99),
        "trimmed_min": min(trimmed), "trimmed_max": max(trimmed),
        "trimmed_avg": avg, "trimmed_sample_stddev": stddev,
    }


def print_stats(title, data):
    stats = calc_trimmed_stats(data, TRIM_FAST_RATIO, TRIM_SLOW_RATIO)
    print(f"\n===== {title} =====")
    if not stats:
        print("no successful data")
        return
    print("----- raw -----")
    print(f"count {stats['raw_count']} | min {stats['raw_min']:.2f} | avg {stats['raw_avg']:.2f}"
          f" | median {stats['raw_median']:.2f} | p90 {stats['raw_p90']:.2f}"
          f" | p95 {stats['raw_p95']:.2f} | p99 {stats['raw_p99']:.2f}"
          f" | max {stats['raw_max']:.2f} (ms)")
    print("----- trimmed -----")
    print(f"trim fast {TRIM_FAST_RATIO*100:.0f}% ({stats['trim_fast_count']}) | "
          f"trim slow {TRIM_SLOW_RATIO*100:.0f}% ({stats['trim_slow_count']}) | "
          f"used {stats['used_count']}")
    print(f"min {stats['trimmed_min']:.2f} | avg {stats['trimmed_avg']:.2f} | "
          f"max {stats['trimmed_max']:.2f} | std {stats['trimmed_sample_stddev']:.2f} (ms)")


# ===== benchmark one query =====
def benchmark(cluster, name, sql):
    print("\n" + "=" * 70)
    print(f"Benchmark: {name}")
    print("=" * 70)
    server_timings, client_timings, failures = [], [], []

    def run_once():
        start = time.perf_counter()
        result = cluster.query(sql, QueryOptions(
            timeout=timedelta(seconds=TIMEOUT_SECONDS), metrics=True, profile="timings"))
        rows = list(result)
        client_ms = (time.perf_counter() - start) * 1000
        exec_ms = result.metadata().metrics().execution_time().total_seconds() * 1000
        return client_ms, exec_ms, len(rows)

    for i in range(WARMUP):
        try:
            c, e, r = run_once()
            print(f"[warmup {i+1}] exec={e:.2f} ms (rows={r})")
        except Exception as ex:
            print(f"[warmup {i+1}] FAIL {ex}")
        time.sleep(SLEEP_SECONDS)

    for i in range(1, RUNS + 1):
        try:
            client_ms, exec_ms, rows = run_once()
            client_timings.append(client_ms)
            server_timings.append(exec_ms)
            if PRINT_EACH_RUN:
                print(f"[{i:03d}] exec={exec_ms:8.2f} ms | client={client_ms:8.2f} ms | rows={rows}")
        except Exception as ex:
            failures.append((i, str(ex)))
            print(f"[{i:03d}] FAIL {ex}")
        time.sleep(SLEEP_SECONDS)

    print_stats(f"{name} -- SERVER execution time", server_timings)
    print_stats(f"{name} -- CLIENT total time", client_timings)
    print(f"\nfailures: {len(failures)}")
    for f in failures[:5]:
        print(f)


def main():
    if not PASSWORD:
        raise SystemExit("Set COUCHBASE_PASSWORD env var before running.")
    print(f"Start test at {datetime.now()}")
    print(f"Query source : {os.path.abspath(QUERY_ROOT)}")
    print(f"Target bucket: {BUCKET_NAME} / scope: {SCOPE_NAME}")
    print("Timing source: metadata().metrics().execution_time() (server-side only)")
    print(f"RUNS={RUNS} WARMUP={WARMUP} SLEEP={SLEEP_SECONDS}s "
          f"TRIM fast={TRIM_FAST_RATIO} slow={TRIM_SLOW_RATIO}")

    cluster = Cluster(CONN_STR, ClusterOptions(PasswordAuthenticator(USERNAME, PASSWORD)))
    cluster.wait_until_ready(timedelta(seconds=10))

    for q in QUERIES:
        path = os.path.join(QUERY_ROOT, q["file"])
        if not os.path.exists(path):
            print(f"\n[skip] {q['name']} -- query file not found: {path}")
            continue
        sql = load_query(path)
        print(f"\n# {q['name']}")
        print(f"  source: {os.path.relpath(path, HERE)}")
        benchmark(cluster, q["name"], sql)

    print("\nBenchmark complete.")


if __name__ == "__main__":
    main()
