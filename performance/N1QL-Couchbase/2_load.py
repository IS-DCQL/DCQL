#!/usr/bin/env python3
"""Step 2 -- create Couchbase collections, import the converted documents, build indexes.

Reads the JSON collection files produced by 1_convert.py (./document/<domain>/*.json) and
loads them into a single Couchbase bucket (default `dcql`, scope `_default`):

    biomedical:       cases               (from document/biomedical/cases.json)
    organic-polymer:  materials_library   (from document/organic-polymer/materials_library.json)
                      processing_logs     (from document/organic-polymer/processing_logs.json)
                      pa6t_library        (from document/organic-polymer/pa6t_library.json)

It carries over the real loading logic of the original import_medical.py / import_material.py:
collection creation, KV-ready probing (avoids key_value_collection_outdated), batched threaded
upserts with retry, then GSI secondary-index creation + ONLINE wait. The indexes mirror the
fields touched by the §6.2 conciseness N1QL queries (English keys produced by 1_convert.py),
which 3_benchmark.py executes.

Connection / behaviour via env vars (defaults shown):
    CB_CONN_STR        couchbase://127.0.0.1
    CB_USERNAME        admin
    COUCHBASE_PASSWORD (no default -- must be set)
    CB_BUCKET          dcql
    CB_SCOPE           _default
"""
import os
import time
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions, UpsertOptions, QueryOptions
from couchbase.management.collections import CollectionSpec

from json_array_to_ndjson import iter_json_docs

HERE = os.path.dirname(os.path.abspath(__file__))

# ========== CONFIG (override via env) ==========
CONN_STR = os.environ.get("CB_CONN_STR", "couchbase://127.0.0.1")
USERNAME = os.environ.get("CB_USERNAME", "admin")
PASSWORD = os.environ.get("COUCHBASE_PASSWORD", "")

BUCKET_NAME = os.environ.get("CB_BUCKET", "dcql")
SCOPE_NAME = os.environ.get("CB_SCOPE", "_default")

DOC_DIR = os.environ.get("CONVERT_OUT_DIR", os.path.join(HERE, "document"))

BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "500"))
WORKERS = int(os.environ.get("WORKERS", "8"))
UPSERT_RETRIES = int(os.environ.get("UPSERT_RETRIES", "8"))
UPSERT_TIMEOUT_SECONDS = 30
QUERY_TIMEOUT_SECONDS = 600
WAIT_AFTER_COLLECTION_CREATE_SECONDS = 10
# ===============================================

# Per-collection load plan: source json (relative to DOC_DIR), the doc-id field path, and
# the GSI indexes used by the §6.2 / §6.4 N1QL queries.
PLAN = [
    {
        "collection": "cases",
        "file": os.path.join("biomedical", "cases.json"),
        # T2 filters on case_id; document id == case_id keeps it stable.
        "id_path": ["case_id"],
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_cases_case_id ON {ks}(case_id)",
            "CREATE INDEX IF NOT EXISTS idx_cases_project ON {ks}(project.project_id)",
            "CREATE INDEX IF NOT EXISTS idx_cases_vital ON {ks}(demographic.vital_status)",
            # T3 diagnoses[] ANY ... vital_status / LOWER(primary_diagnosis)
            "CREATE INDEX IF NOT EXISTS idx_cases_diag ON {ks}("
            "DISTINCT ARRAY [d.vital_status, LOWER(d.primary_diagnosis)] FOR d IN diagnoses END)",
            # T3 samples[] ANY ... sample_type / preservation_method
            "CREATE INDEX IF NOT EXISTS idx_cases_sample ON {ks}("
            "DISTINCT ARRAY [s.sample_type, s.preservation_method] FOR s IN samples END)",
            # T3 deep samples -> portions -> analytes -> aliquots
            "CREATE INDEX IF NOT EXISTS idx_cases_analyte ON {ks}("
            "DISTINCT ARRAY [a.analyte_type, al.concentration] "
            "FOR s IN samples FOR p IN s.portions FOR a IN p.analytes FOR al IN a.aliquots END)",
        ],
    },
    {
        "collection": "materials_library",
        "file": os.path.join("organic-polymer", "materials_library.json"),
        # T3 joins materials_library.basic_info.name == processing_logs.material_name,
        # so key the document on basic_info.name.
        "id_path": ["basic_info", "name"],
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_mat_name ON {ks}(basic_info.name)",
            "CREATE INDEX IF NOT EXISTS idx_mat_category ON {ks}(basic_info.category)",
            "CREATE INDEX IF NOT EXISTS idx_mat_samples ON {ks}("
            "DISTINCT ARRAY [s.thermal.glass_temperature, s.mechanical.tensile_strength] "
            "FOR s IN samples END)",
            "CREATE INDEX IF NOT EXISTS idx_mat_first_sample ON {ks}("
            "samples[0].thermal.glass_temperature, basic_info.name)",
        ],
    },
    {
        "collection": "processing_logs",
        "file": os.path.join("organic-polymer", "processing_logs.json"),
        "id_path": ["meta", "data_id"],
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_proc_data_id ON {ks}(meta.data_id)",
            "CREATE INDEX IF NOT EXISTS idx_proc_alpha ON {ks}("
            "WAXD_result.alpha_crystallinity, meta.data_id)",
            "CREATE INDEX IF NOT EXISTS idx_proc_material_name ON {ks}(material_name)",
            "CREATE INDEX IF NOT EXISTS idx_proc_injection ON {ks}("
            "DISTINCT ARRAY stage FOR stage IN machine_settings.injection.stages END)",
        ],
    },
    {
        "collection": "pa6t_library",
        "file": os.path.join("organic-polymer", "pa6t_library.json"),
        "id_path": ["doc_id"],
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_pa6t_copolymer ON {ks}("
            "composition_variation.copolymer)",
            "CREATE INDEX IF NOT EXISTS idx_pa6t_temp ON {ks}(temperature)",
        ],
    },
]


# ===== connect =====
def connect():
    cluster = Cluster(CONN_STR, ClusterOptions(PasswordAuthenticator(USERNAME, PASSWORD)))
    cluster.wait_until_ready(timedelta(seconds=10))
    return cluster


# ===== collection management (from import_material.py) =====
def collection_exists(bucket, collection_name):
    for s in bucket.collections().get_all_scopes():
        if s.name == SCOPE_NAME:
            for c in s.collections:
                if c.name == collection_name:
                    return True
    return False


def ensure_collection(bucket, collection_name):
    if collection_name == "_default" or collection_exists(bucket, collection_name):
        print(f"  collection already exists: {collection_name}")
        return
    print(f"  creating collection: {BUCKET_NAME}.{SCOPE_NAME}.{collection_name}")
    try:
        bucket.collections().create_collection(
            CollectionSpec(collection_name, scope_name=SCOPE_NAME))
    except Exception as e:
        msg = str(e).splitlines()[0]
        if "already exists" not in msg.lower() and "collection exists" not in msg.lower():
            raise
    # wait until visible
    start = time.time()
    while time.time() - start < 90:
        if collection_exists(bucket, collection_name):
            return
        time.sleep(1)
    raise RuntimeError(f"collection not visible after create: {collection_name}")


def wait_kv_ready(cluster, bucket, collection_name, timeout_seconds=120):
    """Wait for the KV service to recognise the collection (key_value_collection_outdated)."""
    coll = bucket.scope(SCOPE_NAME).collection(collection_name)
    probe_id = f"__probe__::{collection_name}"
    start = time.time()
    while time.time() - start < timeout_seconds:
        try:
            coll.upsert(probe_id, {"type": "probe", "ts": time.time()},
                        UpsertOptions(timeout=timedelta(seconds=10)))
            try:
                cluster.query(
                    f'DELETE FROM `{BUCKET_NAME}`.`{SCOPE_NAME}`.`{collection_name}` '
                    f'USE KEYS "{probe_id}"',
                    QueryOptions(timeout=timedelta(seconds=30))).execute()
            except Exception:
                pass
            return True
        except Exception:
            time.sleep(2)
    raise RuntimeError(f"collection KV not writable: {collection_name}")


# ===== document id =====
def extract_doc_id(doc, id_path, index):
    cur = doc
    for key in id_path:
        if not isinstance(cur, dict):
            cur = None
            break
        cur = cur.get(key)
    if cur is not None and str(cur).strip():
        return str(cur).strip()
    # fallback for rows lacking the natural key (e.g. duplicate / null names)
    return f"{id_path[-1]}::{index}"


# ===== batched threaded upsert (from the import scripts) =====
def write_batch(bucket, collection_name, batch):
    coll = bucket.scope(SCOPE_NAME).collection(collection_name)
    success = failed = 0
    for doc_id, doc in batch:
        for attempt in range(UPSERT_RETRIES):
            try:
                coll.upsert(doc_id, doc,
                            UpsertOptions(timeout=timedelta(seconds=UPSERT_TIMEOUT_SECONDS)))
                success += 1
                break
            except Exception as e:
                if attempt == UPSERT_RETRIES - 1:
                    failed += 1
                    print(f"  upsert failed {collection_name}/{doc_id}: {e}")
                else:
                    msg = str(e)
                    time.sleep(2 + attempt if "key_value_collection_outdated" in msg
                               else 0.5 + attempt * 0.5)
    return success, failed


def import_collection(bucket, collection_name, path, id_path):
    print(f"  importing {path} -> {BUCKET_NAME}.{SCOPE_NAME}.{collection_name}")
    batch, futures, processed = [], [], 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        for index, doc in enumerate(iter_json_docs(path), start=1):
            doc_id = extract_doc_id(doc, id_path, index)
            batch.append((doc_id, doc))
            processed += 1
            if len(batch) >= BATCH_SIZE:
                futures.append(executor.submit(write_batch, bucket, collection_name, batch.copy()))
                batch = []
        if batch:
            futures.append(executor.submit(write_batch, bucket, collection_name, batch.copy()))
        total_success = total_failed = 0
        for fut in as_completed(futures):
            s, f = fut.result()
            total_success += s
            total_failed += f
    elapsed = time.time() - t0
    rate = total_success / elapsed if elapsed > 0 else 0
    print(f"  imported {total_success} docs ({total_failed} failed) in {elapsed:.2f}s "
          f"({rate:.0f} docs/s)")


# ===== indexes =====
def keyspace(collection_name):
    return f"`{BUCKET_NAME}`.`{SCOPE_NAME}`.`{collection_name}`"


def create_indexes(cluster, collection_name, index_templates):
    ks = keyspace(collection_name)
    cluster.query(f"CREATE PRIMARY INDEX IF NOT EXISTS ON {ks}",
                  QueryOptions(timeout=timedelta(seconds=QUERY_TIMEOUT_SECONDS))).execute()
    for tmpl in index_templates:
        sql = tmpl.format(ks=ks)
        try:
            cluster.query(sql, QueryOptions(
                timeout=timedelta(seconds=QUERY_TIMEOUT_SECONDS))).execute()
        except Exception as e:
            print(f"  index skipped: {str(e).splitlines()[0]}")
    print(f"  created {len(index_templates) + 1} indexes (incl. primary)")


def wait_indexes_online(cluster):
    print("\nWaiting for indexes ONLINE...")
    names = [item["collection"] for item in PLAN]
    sql = (f'SELECT keyspace_id, name, state FROM system:indexes '
           f'WHERE bucket_id = "{BUCKET_NAME}" AND scope_id = "{SCOPE_NAME}" '
           f'AND keyspace_id IN {names}')
    while True:
        rows = list(cluster.query(sql, QueryOptions(
            timeout=timedelta(seconds=QUERY_TIMEOUT_SECONDS))))
        pending = [r for r in rows if r.get("state") != "online"]
        if not pending:
            print("All indexes ONLINE")
            return
        time.sleep(2)


def main():
    if not PASSWORD:
        raise SystemExit("Set COUCHBASE_PASSWORD env var before running.")
    cluster = connect()
    bucket = cluster.bucket(BUCKET_NAME)

    print(f"Bucket: {BUCKET_NAME} / scope: {SCOPE_NAME}\n")

    # 1. create collections + wait for KV readiness
    print("== creating collections ==")
    for item in PLAN:
        ensure_collection(bucket, item["collection"])
    print(f"\nWaiting {WAIT_AFTER_COLLECTION_CREATE_SECONDS}s for metadata propagation...")
    time.sleep(WAIT_AFTER_COLLECTION_CREATE_SECONDS)
    for item in PLAN:
        wait_kv_ready(cluster, bucket, item["collection"])

    # 2. import each collection (idempotent: clear first)
    print("\n== importing documents ==")
    for item in PLAN:
        path = os.path.join(DOC_DIR, item["file"])
        if not os.path.exists(path):
            print(f"[skip] {item['collection']} -- {path} not found (run 1_convert.py first)")
            continue
        ks = keyspace(item["collection"])
        cluster.query(f"CREATE PRIMARY INDEX IF NOT EXISTS ON {ks}",
                      QueryOptions(timeout=timedelta(seconds=QUERY_TIMEOUT_SECONDS))).execute()
        cluster.query(f"DELETE FROM {ks}",
                      QueryOptions(timeout=timedelta(seconds=QUERY_TIMEOUT_SECONDS))).execute()
        import_collection(bucket, item["collection"], path, item["id_path"])

    print("\nWaiting for data to settle...")
    time.sleep(5)

    # 3. indexes
    print("\n== creating indexes ==")
    for item in PLAN:
        if not os.path.exists(os.path.join(DOC_DIR, item["file"])):
            continue
        print(f"  {item['collection']}:")
        create_indexes(cluster, item["collection"], item["indexes"])
    wait_indexes_online(cluster)

    print("\nLoad finished. Run 3_benchmark.py next.")


if __name__ == "__main__":
    main()
