#!/usr/bin/env python3
"""DCM schema (template) structure for the stainless-steel data (Table 2, "DCM structure").

DCQL stores data under DCM **schemas** (templates), so this emits one DCM template per
document collection -- the schema count equals the document-collection count. Output is the
native DCM template format: every attribute maps to {"_type", "r", optional "_unit", and
nested sub-attributes for container/array types}; "_type" uses the English DCM type names
(string, number, range, choice, table, container, array, generator, image, file). The
template is inferred from the converted document data (run to_document.py first).
"""
import json, os
HERE = os.path.dirname(__file__)

# (document file under document/, schema name)
COLLECTIONS = [("mechanical_properties.json", "mechanical_properties"), ("pitting_corrosion.json", "pitting_corrosion")]


def required(values):
    return len(values) > 0 and all(v is not None for v in values)


def node_for(name, values):
    """Infer a DCM template node for attribute `name` from its values across all docs."""
    nonnull = [v for v in values if v is not None]
    req = required(values)
    if any(isinstance(v, dict) for v in nonnull):                  # container
        node = {"_type": "container", "r": req}
        keys = []
        for v in nonnull:
            if isinstance(v, dict):
                for k in v:
                    if k not in keys:
                        keys.append(k)
        for k in keys:
            node[k] = node_for(k, [v.get(k) if isinstance(v, dict) else None for v in nonnull])
        return node
    if any(isinstance(v, list) for v in nonnull):                  # array (element under repeated key)
        elems = []
        for v in nonnull:
            if isinstance(v, list):
                elems.extend(v)
        node = {"_type": "array", "r": req}
        node[name] = node_for(name, elems) if elems else {"_type": "string", "r": False}
        return node
    if any(isinstance(v, bool) for v in nonnull):                  # scalar
        t = "choice"
    elif nonnull and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in nonnull):
        t = "number"
    else:
        t = "string"
    return {"_type": t, "r": req}


def build_template(docs, tid):
    keys = []
    for d in docs:
        for k in d:
            if k not in keys:
                keys.append(k)
    tpl = {"_id": tid}
    for k in keys:
        tpl[k] = node_for(k, [d.get(k) for d in docs])
    return tpl


def main():
    out = os.path.join(HERE, "schema")
    os.makedirs(out, exist_ok=True)
    for tid, (doc_file, name) in enumerate(COLLECTIONS, 1):
        docs = json.load(open(os.path.join(HERE, "document", doc_file), encoding="utf-8"))
        tpl = build_template(docs, tid)
        json.dump({"dataset": {"name": name}, "template": tpl},
                  open(os.path.join(out, name + ".schema.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        attrs = [k for k in tpl if not k.startswith("_")]
        print(f"schema {name:22} {len(attrs)} top-level attributes")
    print(f"total schemas: {len(COLLECTIONS)}")


if __name__ == "__main__":
    main()
