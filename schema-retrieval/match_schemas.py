#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§6.6 (RQ4) schema-reuse case study — offline reproduction of the schema-level query.

The case study itself is run on the platform: the query in `query.dcql` is parsed, validated,
translated into a schema-metadata index request and evaluated by the NMDMS read side, exactly
as Section 5 describes, and the seven schemas under `schemas/` are what it returns. This script
is NOT that pipeline. It re-implements the query's path/type semantics in plain Python so that
a reader without access to the platform can reproduce the returned set and the per-field
grading of Table rq4 from the shipped schemas alone.

It exports each candidate schema to a path/type representation, evaluates the three query
conditions to decide whether the schema is *returned*, and then grades every one of the six
required fields along the three dimensions a DCQL schema condition constrains — attribute
name, nesting path, and DCM type — instead of a binary hit/miss:

    exact    (score 1.0)  name, path, and type all match
    var_path (score 0.5)  a same-named field of the required type sits at a different path
    var_type (score 0.5)  the required path exists but carries a different DCM type
    missing  (score 0.0)  no corresponding field

Field coverage is the mean field score; the reuse decision follows fixed coverage thresholds
(reuse directly / reuse with minor extension / partial reference / not reusable). Results go
to `candidates.csv` (the per-field match matrix of Table rq4) and the summary (K returned,
R reusable, top-k precision) is printed. The full schema-library size N is a property of the
real NMDMS library (> 2000 schemas) and is documented in `README.md`, not derived here.

INPUT: `SCHEMA_LIB` (env var or the constant below) points at a folder of DCM schema
templates. The bundled `schemas/` folder holds the K = 7 candidates the query returned, so
running this script reproduces `candidates.csv` and Table rq4 verbatim.
Each file is a DCM template `{ "_id": …, "<attr>": {"_type": …, "r": …, <nested>}, … }`,
optionally wrapped as `{"dataset": …, "template": {…}}` — the format emitted by
`../conciseness/_<domain>_conversion/to_schema.py`.
"""
import json, os, csv, glob

HERE = os.path.dirname(os.path.abspath(__file__))

# The K returned candidates ship under schemas/; point this at the full exported NMDMS
# schema library to run over the real library instead.
SCHEMA_LIB = os.environ.get("SCHEMA_LIB", os.path.join(HERE, "schemas"))

# Real NMDMS schema-library size (documented, not derivable from the returned candidates).
LIBRARY_SIZE_N = "> 2000"

# The 6 required fields of the new stainless-steel corrosion+mechanical model (name, path,
# DCM type). Paths follow the paper: an attribute key addresses a child of a container OR of a
# generator (Definition 3), so the generator contributes its own segment -- perform.corr.* /
# perform.mech.*, exactly as the paper writes the running query.
REQUIRED = [
    ("info.batch", "string"),
    ("info.comp", "string"),                 # Array{String} -> element type string
    ("perform.corr.corrInfo.elec", "number"),
    ("perform.corr.corrInfo.density", "number"),
    ("perform.mech.mechInfo.yield", "number"),
    ("perform.mech.mechInfo.hard", "number"),
]

SCORE = {"exact": 1.0, "var_path": 0.5, "var_type": 0.5, "missing": 0.0}


def flatten(node, prefix=""):
    """Flatten a DCM template node to {dotted_path: _type}.

    - container: recurse by attribute name.
    - array / table: descend into the element (stored under the repeated key), keeping the
      collection's path (so a table column perform.corr.corrInfo.elec flattens to that path).
    - generator: contributes its own segment, like a container. Definition 3 makes an
      attribute key address a child of a container-type OR generator-type node, so the
      branches of `perform` are reached as perform.corr.* / perform.mech.*.
    """
    out = {}
    if not isinstance(node, dict):
        return out
    t = node.get("_type")
    if t in (None, "container"):
        for k, sub in node.items():
            if k.startswith("_") or k == "r":
                continue
            out.update(flatten(sub, f"{prefix}.{k}" if prefix else k))
    elif t in ("array", "table"):
        for k, sub in node.items():
            if k.startswith("_") or k == "r":
                continue
            out.update(flatten(sub, prefix))
    elif t == "generator":                       # like a container: each branch is a keyed child
        for k, sub in node.items():
            if k.startswith("_") or k == "r":
                continue
            out.update(flatten(sub, f"{prefix}.{k}" if prefix else k))
    else:                                         # primitive leaf (string/number/range/...)
        out[prefix] = t
    return out


def load_template(path):
    d = json.load(open(path, encoding="utf-8"))
    return d.get("template", d)


def leaf(path):
    return path.split(".")[-1]


def grade(req_path, req_type, paths):
    """Grade one required field against a schema's {path: type}: exact / var_path / var_type /
    missing (see module docstring)."""
    if req_path in paths:
        return "exact" if paths[req_path] == req_type else "var_type"
    lf = leaf(req_path)
    for p, ty in paths.items():                   # same leaf name and type at a different path
        if leaf(p) == lf and ty == req_type:
            return "var_path"
    return "missing"


def satisfies_query(paths):
    """Scheme C: perform.corr.corrInfo.elec = Number  AND  ANY yield = Number  AND  EXIST
    perform.corr.corrInfo.density. A schema is *returned* iff it satisfies all three.

    This mirrors in Python what the platform's schema-metadata index evaluates; it is a
    reproduction of that result, not the execution path used for the case study."""
    c1 = paths.get("perform.corr.corrInfo.elec") == "number"                    # exact path + type
    c2 = any(leaf(p) == "yield" and ty == "number" for p, ty in paths.items())  # ANY yield = Number
    c3 = "perform.corr.corrInfo.density" in paths                               # EXIST (any type)
    return c1 and c2 and c3


def reuse_decision(cov):
    if cov >= 1.0:
        return "reuse directly"
    if cov >= 0.7:
        return "reuse with minor extension"
    if cov >= 0.4:
        return "partial reference"
    return "not reusable"


def main():
    files = sorted(glob.glob(os.path.join(SCHEMA_LIB, "**", "*.json"), recursive=True))
    if not files:
        print(f"[TODO] no schema files under SCHEMA_LIB={SCHEMA_LIB}. "
              "Point it at your exported DCM schema library (or the bundled schemas/) and re-run.")
        return
    rows = []
    for f in files:
        paths = flatten(load_template(f))
        if not satisfies_query(paths):
            continue                              # not returned by the schema query
        verdicts = {rp: grade(rp, rt, paths) for rp, rt in REQUIRED}
        cov = round(sum(SCORE[verdicts[rp]] for rp, _ in REQUIRED) / len(REQUIRED), 2)
        row = {"candidate_schema": os.path.splitext(os.path.basename(f))[0]}
        row.update({rp: verdicts[rp] for rp, _ in REQUIRED})
        row["coverage"] = f"{cov:.2f}"
        row["reuse_decision"] = reuse_decision(cov)
        rows.append(row)
    rows.sort(key=lambda r: -float(r["coverage"]))

    fields = ["candidate_schema"] + [rp for rp, _ in REQUIRED] + ["coverage", "reuse_decision"]
    out = os.path.join(HERE, "candidates.csv")
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    K = len(rows)
    R = sum(1 for r in rows if float(r["coverage"]) >= 0.4)
    prec = f"{R / K:.0%}" if K else "n/a"
    print(f"library size N = {LIBRARY_SIZE_N} (real NMDMS library; see README.md)")
    print(f"returned candidates K = {K} | reusable (coverage >= 0.4) R = {R} | top-k precision = {prec}")
    print(f"wrote {out} (per-field match matrix, Table rq4)")


if __name__ == "__main__":
    main()
