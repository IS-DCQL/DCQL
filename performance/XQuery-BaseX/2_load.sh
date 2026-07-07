#!/usr/bin/env bash
# Step 2 — create the BaseX databases + indexes for the §6.4 performance run.
#
# Builds FOUR databases that the benchmark queries open:
#   tcga_cases         (XML)  <- prepared_for_basex.xml  (biomedical, merged cases)
#   materials_library  (JSON) <- materials_library_en.json
#   processing_logs    (JSON) <- processing_logs_en.json
#   pa6t_library       (JSON) <- pa6t_library_en.json
#
# The polymer collections are imported with BaseX's native JSON parser, so they are
# served as the map/<string key>/<number key> form the polymer XQuery queries walk
# with db:get(...)//map. A TEXT index is built on the predicate fields used by the
# T2/T3 queries (same index strategy as the original create_db_and_indexes.bxs).
#
# Run after 1_convert.py, from this folder:  ./2_load.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

BASEX="${BASEX:-./bin/basex}"
if [ ! -x "$BASEX" ]; then
    if command -v basex >/dev/null 2>&1; then
        BASEX="$(command -v basex)"
    else
        echo "Error: BaseX executable not found (set BASEX=... or put ./bin/basex)" >&2
        exit 1
    fi
fi

LOAD_BXS="$HERE/create_db_and_indexes.bxs"
if [ ! -f "$LOAD_BXS" ]; then
    echo "Error: $LOAD_BXS not found" >&2
    exit 1
fi

echo "Loading BaseX databases + indexes via $(basename "$LOAD_BXS") ..."
"$BASEX" "$LOAD_BXS"
echo "Done. Databases created: tcga_cases, materials_library, processing_logs, pa6t_library"
