#!/usr/bin/env python3
"""Document structure for the stainless-steel data: 2 collections (Table 2).

Keeps the aggregated (nested) form. The two source files map one-to-one to two
collections, each document = one {meta, content} record.

    collection 1: mechanical_properties   (composition + mechanical)
    collection 2: pitting_corrosion        (corrosion experiments)
"""
import json, os
HERE = os.path.dirname(__file__)

COLLECTIONS = [
    ("stainless_mechanical_en.json", "mechanical_properties"),
    ("stainless_pitting_en.json",    "pitting_corrosion"),
]

def main():
    out_dir = os.path.join(HERE, "document")
    os.makedirs(out_dir, exist_ok=True)
    for src, coll in COLLECTIONS:
        d = json.load(open(os.path.join(HERE, src), encoding="utf-8"))
        docs = d["data"]                      # list of {meta, content}
        json.dump(docs, open(os.path.join(out_dir, coll + ".json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print(f"collection {coll}: {len(docs)} documents")

if __name__ == "__main__":
    main()
