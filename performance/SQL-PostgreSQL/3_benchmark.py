#!/usr/bin/env python3
"""
Step 3 — Run and time the T2/T3 queries (§6.4 latency measurement).

The four query statements are LOADED FROM the conciseness folder (not hardcoded
here), so the benchmark always runs the exact same SQL that is reported there:

  ../../conciseness/SQL/biomedical/T2.sql
  ../../conciseness/SQL/biomedical/T3.sql
  ../../conciseness/SQL/organic-polymer/T2.sql
  ../../conciseness/SQL/organic-polymer/T3.sql

Timing methodology (unchanged from the original query_performance_test.py):
  * optimizer pinned to Nested Loop + Index Scan (cost params, no parallelism);
  * server-side execution via psycopg2 with perf_counter around execute+fetch;
  * 5 warm-up runs (discarded) + 25 measured runs (30 total) per query;
  * mean / median / stddev / CV reported for the measured runs.

DB credentials come from environment variables (no hardcoded password).
Run order: 1_convert.py -> 2_load.py -> 3_benchmark.py
"""

import os
import psycopg2
import time
import logging
from statistics import mean, median, stdev

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_CONFIG = {
    'dbname': os.environ.get('PG_DATABASE', 'clinical_db'),
    'user': os.environ.get('PG_USER', 'sal'),
    'password': os.environ.get('PG_PASSWORD', ''),
    'host': os.environ.get('PG_HOST', 'localhost'),
    'port': int(os.environ.get('PG_PORT', 5432)),
}

# Source of the four query statements (read from the conciseness folder, not embedded here)
HERE = os.path.dirname(os.path.abspath(__file__))
QUERY_DIR = os.path.normpath(os.path.join(HERE, '..', '..', 'conciseness', 'SQL'))

QUERIES = [
    ('biomedical', 'T2', os.path.join(QUERY_DIR, 'biomedical', 'T2.sql')),
    ('biomedical', 'T3', os.path.join(QUERY_DIR, 'biomedical', 'T3.sql')),
    ('organic-polymer', 'T2', os.path.join(QUERY_DIR, 'organic-polymer', 'T2.sql')),
    ('organic-polymer', 'T3', os.path.join(QUERY_DIR, 'organic-polymer', 'T3.sql')),
]


def load_query(path):
    """Read the query text from a .sql file."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read().strip()


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def set_optimizer_for_nested_loop(conn):
    """Bias the optimizer toward Nested Loop + Index Scan (same as the original script)."""
    cur = conn.cursor()

    cur.execute("SET enable_nestloop = on")
    cur.execute("SET enable_hashjoin = on")
    cur.execute("SET enable_mergejoin = on")

    cur.execute("SET random_page_cost = 1.0")
    cur.execute("SET seq_page_cost = 10.0")
    cur.execute("SET cpu_tuple_cost = 0.01")
    cur.execute("SET cpu_index_tuple_cost = 0.005")

    cur.execute("SET enable_seqscan = on")
    cur.execute("SET enable_indexscan = on")
    cur.execute("SET enable_indexonlyscan = on")
    cur.execute("SET enable_bitmapscan = on")

    cur.execute("SET max_parallel_workers_per_gather = 0")

    cur.execute("SET work_mem = '256MB'")
    cur.execute("SET effective_cache_size = '4GB'")

    conn.commit()
    cur.close()

    logger.info("Set: prefer Nested Loop + Index Scan")


def reset_settings(conn):
    """Reset all settings."""
    cur = conn.cursor()
    cur.execute("RESET ALL")
    conn.commit()
    cur.close()
    logger.info("All settings reset")


def execute_query(conn, query):
    """Execute the query and measure server-side execution time (execute + fetch)."""
    cur = conn.cursor()

    # set the statement timeout (60 seconds)
    cur.execute("SET statement_timeout = 60000")

    start = time.perf_counter()
    cur.execute(query)
    results = cur.fetchall()
    end = time.perf_counter()

    elapsed_ms = (end - start) * 1000
    row_count = len(results)

    cur.execute("SET statement_timeout = 0")
    cur.close()
    return elapsed_ms, row_count


def run_performance_test(conn, query, runs=30, warm_up_count=5):
    """Run the performance test (default: 5 warm-up + 25 measured = 30 runs)."""
    logger.info(f"\nStarting performance test ({warm_up_count} warm-up + {runs - warm_up_count} measured = {runs} runs total)...")

    # warm-up (discarded)
    logger.info(f"Warming up ({warm_up_count} runs)...")
    for i in range(warm_up_count):
        execute_query(conn, query)
        time.sleep(0.3)

    times = []
    row_counts = []

    measured = runs - warm_up_count
    for i in range(measured):
        elapsed_ms, row_count = execute_query(conn, query)
        times.append(elapsed_ms)
        row_counts.append(row_count)
        logger.info(f"  run #{i+1}: {elapsed_ms:.2f} ms, {row_count} rows")

        if (i + 1) % 5 == 0 and i < measured - 1:
            time.sleep(0.5)

    return times, row_counts


def analyze_results(times, row_counts):
    """Analyze the results (measured runs already exclude warm-up)."""
    logger.info("\nStatistics:")
    logger.info(f"  Sample count: {len(times)}")
    avg = mean(times)
    logger.info(f"  Mean time:    {avg:.2f} ms")
    logger.info(f"  Median:       {median(times):.2f} ms")
    if len(times) >= 2:
        sd = stdev(times)
        logger.info(f"  Std dev:      {sd:.2f} ms")
        if avg > 0:
            cv = (sd / avg) * 100
            logger.info(f"  CV:           {cv:.2f}%")
    logger.info(f"  Min:          {min(times):.2f} ms")
    logger.info(f"  Max:          {max(times):.2f} ms")
    logger.info(f"  Mean rows returned: {mean(row_counts):.0f}")
    return avg, mean(row_counts)


def main():
    logger.info("=" * 70)
    logger.info("Step 3: T2/T3 query performance test (query text from the conciseness folder)")
    logger.info("Configuration: 5 warm-up + 25 measured = 30 runs per query")
    logger.info("=" * 70)

    # load the four query statements first
    loaded = []
    for domain, task, path in QUERIES:
        if not os.path.exists(path):
            logger.warning(f"Query file missing: {path} — skipping {domain} {task}")
            continue
        loaded.append((domain, task, load_query(path)))
        logger.info(f"Loaded query: {domain} {task}  <- {path}")

    if not loaded:
        logger.error("No query files found; exiting.")
        return

    conn = None
    summary = []
    try:
        conn = get_db_connection()
        logger.info("Database connection established")

        set_optimizer_for_nested_loop(conn)

        for domain, task, query in loaded:
            logger.info("\n" + "=" * 70)
            logger.info(f"Testing {domain} {task}")
            logger.info("=" * 70)
            logger.info(query)

            times, row_counts = run_performance_test(conn, query, runs=30, warm_up_count=5)
            avg_time, avg_rows = analyze_results(times, row_counts)
            summary.append((domain, task, avg_time, len(times), avg_rows))

        # summary table
        logger.info("\n" + "=" * 70)
        logger.info("Results summary")
        logger.info("=" * 70)
        logger.info("| Domain          | Task | Mean time (ms) | Samples | Mean rows returned |")
        logger.info("|-----------------|------|----------------|---------|--------------------|")
        for domain, task, avg_time, n, avg_rows in summary:
            logger.info(f"| {domain:<15} | {task:<4} | {avg_time:>14.2f} | {n:>7} | {avg_rows:>18.0f} |")
        logger.info("=" * 70)

        # save the results
        out_path = os.path.join(HERE, 'performance_result.txt')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write("SQL/PostgreSQL T2/T3 query performance test results\n")
            f.write("(query text from ../../conciseness/SQL/)\n")
            f.write("=" * 70 + "\n\n")
            f.write("| Domain          | Task | Mean time (ms) | Samples | Mean rows returned |\n")
            f.write("|-----------------|------|----------------|---------|--------------------|\n")
            for domain, task, avg_time, n, avg_rows in summary:
                f.write(f"| {domain:<15} | {task:<4} | {avg_time:>14.2f} | {n:>7} | {avg_rows:>18.0f} |\n")
        logger.info(f"\nResults saved to: {out_path}")

    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        if conn:
            reset_settings(conn)
            conn.close()
            logger.info("\nDatabase connection closed")


if __name__ == "__main__":
    main()
