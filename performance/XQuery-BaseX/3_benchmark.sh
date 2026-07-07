#!/usr/bin/env bash
# Step 3 — hot-cache execution-time benchmark for the XQuery/BaseX §6.4 run.
#
# Times the FOUR §6.2 queries (biomedical T2/T3 + organic-polymer T2/T3). The query
# TEXT is NOT hardcoded here: each query is read verbatim from the conciseness folder
#   ../../conciseness/XQuery/biomedical/{T2,T3}.xq
#   ../../conciseness/XQuery/organic-polymer/{T2,T3}.xq
# and passed straight to BaseX.
#
# Methodology (unchanged): per query run one warm-up (discarded), then RUNS hot runs;
# the execution time is parsed from BaseX's <testsuite ... time="PT..S"> info output.
#
# Run after 2_load.sh, from this folder:  ./3_benchmark.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

RUNS=10
BASEX="${BASEX:-./bin/basex}"
if [ ! -x "$BASEX" ]; then
    if command -v basex >/dev/null 2>&1; then
        BASEX="$(command -v basex)"
    else
        echo "Error: BaseX executable not found (set BASEX=... or put ./bin/basex)" >&2
        exit 1
    fi
fi

# Query sources in the conciseness folder.
CONC="$HERE/../../conciseness/XQuery"
BIO_T2="$CONC/biomedical/T2.xq"
BIO_T3="$CONC/biomedical/T3.xq"
POLY_T2="$CONC/organic-polymer/T2.xq"
POLY_T3="$CONC/organic-polymer/T3.xq"

for q in "$BIO_T2" "$BIO_T3" "$POLY_T2" "$POLY_T3"; do
    if [ ! -f "$q" ]; then
        echo "Error: query file not found: $q" >&2
        exit 1
    fi
done

WORK_DIR="/tmp/basex_exec_bench"
OUT_DIR="$WORK_DIR/hot_outputs"
mkdir -p "$OUT_DIR"

# The biomedical queries are written against the bare /json/_ context, so the
# tcga_cases DB is opened as the query context with `-i`. The polymer queries open
# their databases explicitly via db:get(...), so they need no input context.
BIO_CTX="tcga_cases"

extract_exec_time_sec() {
    local log_file="$1"
    awk '
    {
        if (match($0, /<testsuite[^>]* time="PT[0-9.]+S"/)) {
            s = substr($0, RSTART, RLENGTH); sub(/^.*time="PT/, "", s); sub(/S".*$/, "", s)
            printf("%.9f\n", s); exit
        }
        if (match($0, /<testsuites[^>]* time="PT[0-9.]+S"/)) {
            s = substr($0, RSTART, RLENGTH); sub(/^.*time="PT/, "", s); sub(/S".*$/, "", s)
            printf("%.9f\n", s); exit
        }
        if ($0 ~ /Query executed in/) {
            for (i = 1; i <= NF; i++) {
                if ($i == "in") {
                    val = $(i + 1); unit = $(i + 2); gsub(/[^0-9.]/, "", val)
                    if (unit ~ /ms/) printf("%.9f\n", val / 1000.0); else printf("%.9f\n", val)
                    exit
                }
            }
        }
    }
    ' "$log_file"
}

calc_stats() {
    local file="$1"
    awk '
    { x[NR] = $1; sum += $1 }
    END {
        n = NR
        if (n == 0) { print "No timing data."; exit }
        mean = sum / n
        if (n > 1) { for (i = 1; i <= n; i++) ss += (x[i] - mean) * (x[i] - mean); std = sqrt(ss / (n - 1)) }
        else std = 0
        printf("runs = %d\n", n)
        printf("mean = %.9f s\n", mean)
        printf("mean = %.6f ms\n", mean * 1000)
        printf("sample_stddev = %.9f s\n", std)
        printf("sample_stddev = %.6f ms\n", std * 1000)
    }
    ' "$file"
}

# run_basex <query_file> <input_db_or_empty> <log_file>
run_basex() {
    local query_file="$1" input_db="$2" log_file="$3"
    rm -f "$log_file"
    if [ -n "$input_db" ]; then
        "$BASEX" -t -i "$input_db" "$query_file" > "$log_file" 2>&1
    else
        "$BASEX" -t "$query_file" > "$log_file" 2>&1
    fi
}

# benchmark <label> <query_file> <input_db_or_empty> <time_file>
benchmark() {
    local label="$1" query_file="$2" input_db="$3" time_file="$4"
    rm -f "$time_file"

    echo "Warm-up $label ..."
    run_basex "$query_file" "$input_db" "$OUT_DIR/${label}_warmup.log"

    echo "Hot cache benchmark: $label, $RUNS runs"
    for i in $(seq 1 "$RUNS"); do
        run_basex "$query_file" "$input_db" "$OUT_DIR/${label}_run_$i.log"
        t=$(extract_exec_time_sec "$OUT_DIR/${label}_run_$i.log")
        if [ -z "$t" ]; then
            echo "Error: failed to extract BaseX execution time for $label." >&2
            cat "$OUT_DIR/${label}_run_$i.log" >&2
            exit 1
        fi
        echo "$t" >> "$time_file"
        ms=$(awk -v t="$t" 'BEGIN { printf "%.6f", t * 1000 }')
        echo "$label hot run $i: ${ms} ms"
    done
    echo
}

benchmark "biomedical_T2" "$BIO_T2"  "$BIO_CTX" "$WORK_DIR/biomedical_T2_times.txt"
benchmark "biomedical_T3" "$BIO_T3"  "$BIO_CTX" "$WORK_DIR/biomedical_T3_times.txt"
benchmark "polymer_T2"    "$POLY_T2" ""         "$WORK_DIR/polymer_T2_times.txt"
benchmark "polymer_T3"    "$POLY_T3" ""         "$WORK_DIR/polymer_T3_times.txt"

echo "========== Hot cache BaseX execution-time results =========="
echo;  echo "Biomedical T2:"; calc_stats "$WORK_DIR/biomedical_T2_times.txt"
echo;  echo "Biomedical T3:"; calc_stats "$WORK_DIR/biomedical_T3_times.txt"
echo;  echo "Organic-polymer T2:"; calc_stats "$WORK_DIR/polymer_T2_times.txt"
echo;  echo "Organic-polymer T3:"; calc_stats "$WORK_DIR/polymer_T3_times.txt"
