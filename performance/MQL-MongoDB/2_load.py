#!/usr/bin/env python3
"""Step 2 -- import the converted documents into MongoDB + create indexes.

Reads the JSON collection files produced by 1_convert.py (./document/<domain>/*.json),
bulk-loads each into its MongoDB collection, and builds the indexes used by the §6.4
queries. Carries over the batched bulk_write / index logic of the original import.py
(biomedical `cases`), and extends it to the three organic-polymer collections.

Connection comes from env vars:
    MONGO_URI   (default mongodb://localhost:27017)
    BIO_DB      biomedical database name      (default dcql_bio)
    POLY_DB     organic-polymer database name (default dcql_poly)
"""
import json
import os
import time

from pymongo import MongoClient

try:
    from tqdm import tqdm
except ImportError:  # tqdm optional
    def tqdm(it, **kw):
        return it

HERE = os.path.dirname(os.path.abspath(__file__))

# ========== CONFIG (override via env) ==========
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
BIO_DB = os.environ.get("BIO_DB", "dcql_bio")
POLY_DB = os.environ.get("POLY_DB", "dcql_poly")

DOC_DIR = os.environ.get("CONVERT_OUT_DIR", os.path.join(HERE, "document"))
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "5000"))
# ===============================================

# Per-collection plan: domain dir, db, collection name, json file, and indexes.
# Indexes mirror the fields touched by the §6.2 / §6.4 MQL queries.
PLAN = [
    {
        "domain": "biomedical",
        "db": BIO_DB,
        "collection": "cases",
        "file": "cases.json",
        "indexes": [
            "case_id",
            "project.project_id",
            "demographic.vital_status",
            "diagnoses.vital_status",
            "diagnoses.primary_diagnosis",
            "samples.sample_type",
            "samples.preservation_method",
            "samples.portions.analytes.analyte_type",
        ],
    },
    {
        "domain": "organic-polymer",
        "db": POLY_DB,
        "collection": "materials_library",
        "file": "materials_library.json",
        "indexes": [
            "basic_info.name",
            "basic_info.category",
            "samples.thermal.glass_temperature",
            "samples.mechanical.tensile_strength",
        ],
    },
    {
        "domain": "organic-polymer",
        "db": POLY_DB,
        "collection": "processing_logs",
        "file": "processing_logs.json",
        "indexes": [
            "meta.data_id",
            "material_name",
            "WAXD_result.alpha_crystallinity",
        ],
    },
    {
        "domain": "organic-polymer",
        "db": POLY_DB,
        "collection": "pa6t_library",
        "file": "pa6t_library.json",
        "indexes": [
            "composition_variation.copolymer",
            "temperature",
            "density",
        ],
    },
]


def load_documents(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    for key in ["data", "documents", "records", "items"]:
        if key in data and isinstance(data[key], list):
            return data[key]
    if isinstance(data, dict):
        return [data]
    raise ValueError(f"Unrecognized JSON structure in {path}")


def import_collection(collection, docs):
    processed = 0
    batch = []
    t0 = time.time()
    for doc in tqdm(docs, desc=f"Import {collection.name}"):
        if not isinstance(doc, dict):
            continue
        batch.append(doc)
        if len(batch) >= BATCH_SIZE:
            collection.insert_many(batch, ordered=False)
            processed += len(batch)
            batch.clear()
    if batch:
        collection.insert_many(batch, ordered=False)
        processed += len(batch)
    elapsed = time.time() - t0
    rate = processed / elapsed if elapsed > 0 else 0
    print(f"  imported {processed} docs in {elapsed:.2f}s ({rate:.0f} docs/s)")


def ensure_indexes(collection, fields):
    for field in fields:
        collection.create_index(field)
    print(f"  created {len(fields)} indexes")


def main():
    client = MongoClient(MONGO_URI)
    print(f"MongoDB URI: {MONGO_URI}\n")
    try:
        for item in PLAN:
            path = os.path.join(DOC_DIR, item["domain"], item["file"])
            if not os.path.exists(path):
                print(f"[skip] {item['db']}.{item['collection']} -- {path} not found "
                      f"(run 1_convert.py first)")
                continue
            db = client[item["db"]]
            coll = db[item["collection"]]
            print(f"== {item['db']}.{item['collection']} (from {item['file']}) ==")
            coll.drop()  # idempotent reload
            docs = load_documents(path)
            import_collection(coll, docs)
            ensure_indexes(coll, item["indexes"])
            print()
        print("Load finished. Run 3_benchmark.py next.")
    finally:
        client.close()


if __name__ == "__main__":
    main()
