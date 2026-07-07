#!/usr/bin/env bash
# Step 3 - run + time the T2/T3 queries on RumbleDB, with COLD-cache and HOT-cache timing.
#
# Query TEXT is loaded from the conciseness folder (single source of truth), NOT from local
# .jq files:
#     ../../conciseness/JSONiq/biomedical/T2.jq, T3.jq
#     ../../conciseness/JSONiq/organic-polymer/T2.jq, T3.jq
# Those queries reference documents by bare relative filenames (cases.json, processing_logs.json,
# materials_library.json), so we cd into the staged $WORK_DIR (populated by 2_load.sh) before
# invoking RumbleDB and pass each query file by absolute path.
#
# Timing methodology (same as the original bench_cold.sh / bench_hot.sh):
#   - wallclock via /usr/bin/time -f "%e" (server-side / single-process java -jar run)
#   - HOT:  one warm-up run discarded, then $RUNS timed runs over a primed page cache
#   - COLD: before each timed run, sync + drop_caches (needs sudo); $RUNS timed runs
#   - report runs / mean / sample stddev
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JAR="${JAR:-$HERE/rumbledb-1.22.0-standalone.jar}"
WORK_DIR="${WORK_DIR:-$HERE/work}"
CONCISE="$HERE/../../conciseness/JSONiq"
RUNS="${RUNS:-10}"
DO_COLD="${DO_COLD:-1}"   # set DO_COLD=0 to skip the cold-cache pass (it needs sudo)

# query label -> conciseness query file
QUERIES=(
    "biomedical_T2:$CONCISE/biomedical/T2.jq"
    "biomedical_T3:$CONCISE/biomedical/T3.jq"
    "polymer_T2:$CONCISE/organic-polymer/T2.jq"
    "polymer_T3:$CONCISE/organic-polymer/T3.jq"
)

[ -f "$JAR" ] || { echo "ERROR: RumbleDB jar not found at $JAR (set JAR=...)" >&2; exit 1; }
[ -d "$WORK_DIR" ] || { echo "ERROR: $WORK_DIR not found. Run: bash 2_load.sh" >&2; exit 1; }

# stats over a file of one wallclock-seconds value per line
report_stats() {
    awk '
    { x[NR] = $1; sum += $1 }
    END {
        n = NR; mean = sum / n
        if (n > 1) { for (i = 1; i <= n; i++) ss += (x[i]-mean)*(x[i]-mean); std = sqrt(ss/(n-1)) }
        else std = 0
        printf("    runs = %d\n", n)
        printf("    mean = %.6f s\n", mean)
        printf("    sample_stddev = %.6f s\n", std)
    }' "$1"
}

run_one() {  # $1=query file  $2=times file  $3=mode(hot|cold)
    local qfile="$1" tfile="$2" mode="$3"
    : > "$tfile"
    if [ "$mode" = "hot" ]; then
        # warm-up (discarded)
        ( cd "$WORK_DIR" && java -jar "$JAR" run "$qfile" >/dev/null )
    fi
    for i in $(seq 1 "$RUNS"); do
        if [ "$mode" = "cold" ]; then
            sudo sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches'
        fi
        ( cd "$WORK_DIR" && /usr/bin/time -f "%e" -o /tmp/one_time.txt \
            java -jar "$JAR" run "$qfile" >/dev/null )
        cat /tmp/one_time.txt >> "$tfile"
    done
}

echo "RumbleDB benchmark: $RUNS timed runs per query (jar: $(basename "$JAR"))"
echo "Queries sourced from: $CONCISE"
echo "Working dir (staged docs): $WORK_DIR"
echo

for entry in "${QUERIES[@]}"; do
    label="${entry%%:*}"
    qfile="${entry#*:}"
    [ -f "$qfile" ] || { echo "ERROR: query file not found: $qfile" >&2; exit 1; }

    echo "==================== $label ($qfile) ===================="

    echo "  [HOT cache]"
    hot_times="/tmp/rumbledb_${label}_hot_times.txt"
    run_one "$qfile" "$hot_times" hot
    report_stats "$hot_times"

    if [ "$DO_COLD" = "1" ]; then
        echo "  [COLD cache]  (drops page cache before each run; needs sudo)"
        cold_times="/tmp/rumbledb_${label}_cold_times.txt"
        run_one "$qfile" "$cold_times" cold
        report_stats "$cold_times"
    else
        echo "  [COLD cache]  skipped (DO_COLD=0)"
    fi
    echo
done

echo "All four queries timed (cold + hot)."
