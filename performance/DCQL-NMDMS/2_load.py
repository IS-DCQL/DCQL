#!/usr/bin/env python3
"""DCQL (NMDMS) — index creation + data import (read-path engine).

Creates one index per collection on the NMDMS read engine and bulk-loads the converted
documents from 1_convert.py. Nested arrays (diagnoses, samples, …; samples, …) are mapped
as `nested` so the path predicates in the queries evaluate per-element.

  biomedical:      cases
  organic-polymer: materials_library, processing_logs, pa6t_library
"""
import json, os, glob
from elasticsearch import Elasticsearch, helpers

HOST = os.environ.get("DCQL_HOST", "http://localhost:9200")
HERE = os.path.dirname(os.path.abspath(__file__))
DOC = os.path.join(HERE, "document")

# (index, source file, _id field, nested paths)
INDICES = [
    ("cases", "biomedical/cases.json", "case_id", ["diagnoses", "samples"]),
    ("materials_library", "organic-polymer/materials_library.json", None, ["samples"]),
    ("processing_logs", "organic-polymer/processing_logs.json", None, []),
    ("pa6t_library", "organic-polymer/pa6t_library.json", None, []),
]


def connect():
    es = Elasticsearch(HOST, request_timeout=180,
                       basic_auth=(os.environ.get("DCQL_USER"), os.environ.get("DCQL_PASSWORD"))
                       if os.environ.get("DCQL_PASSWORD") else None)
    if not es.ping():
        raise RuntimeError("Cannot reach the NMDMS read engine; is it running?")
    return es


def create_index(es, name, nested_paths):
    if es.indices.exists(index=name):
        es.indices.delete(index=name)
    props = {p: {"type": "nested"} for p in nested_paths}
    es.indices.create(index=name, mappings={"properties": props} if props else None)


def load(es, name, src, id_field):
    docs = json.load(open(os.path.join(DOC, src), encoding="utf-8"))
    actions = ({"_op_type": "create", "_index": name,
                **({"_id": d.get(id_field)} if id_field else {}), "_source": d} for d in docs)
    ok, _ = helpers.bulk(es, actions, chunk_size=2000, request_timeout=180)
    print(f"index {name}: loaded {ok} documents")


def main():
    es = connect()
    for name, src, id_field, nested in INDICES:
        create_index(es, name, nested)
        load(es, name, src, id_field)
    for name, *_ in INDICES:
        es.indices.refresh(index=name)


if __name__ == "__main__":
    main()
