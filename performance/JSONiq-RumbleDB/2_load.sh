#!/usr/bin/env bash
# Step 2 - stage the converted JSON documents into the working directory RumbleDB queries from.
#
# RumbleDB has no separate "load" step: it reads JSON files directly through json-doc(...).
# The conciseness JSONiq queries reference the documents by BARE relative filenames
# (e.g. json-doc("cases.json"), json-doc("processing_logs.json"), json-doc("materials_library.json")).
# So "loading" here just means placing the files produced by 1_convert.py into a single
# work directory ($WORK_DIR), and the benchmark (3_benchmark.sh) cd's into that directory
# before invoking RumbleDB so those bare paths resolve.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$HERE/data"
WORK_DIR="${WORK_DIR:-$HERE/work}"

DOCS=(cases.json materials_library.json processing_logs.json pa6t_library.json)

if [ ! -d "$DATA_DIR" ]; then
    echo "ERROR: $DATA_DIR not found. Run: python3 1_convert.py" >&2
    exit 1
fi

mkdir -p "$WORK_DIR"
for f in "${DOCS[@]}"; do
    if [ ! -f "$DATA_DIR/$f" ]; then
        echo "ERROR: missing $DATA_DIR/$f. Run: python3 1_convert.py" >&2
        exit 1
    fi
    cp -f "$DATA_DIR/$f" "$WORK_DIR/$f"
    echo "staged $f -> $WORK_DIR/$f"
done

echo "Done. Documents staged in $WORK_DIR (queried via bare relative filenames)."
