#!/usr/bin/env python3
"""Object structure for the biomedical data: 8 persistent classes (Table 2).

Object-database model used by OQL/JPQL.  Eight classes, each owning its extent:
    Project, Case, Demographic, Diagnosis, Sample, Portion, Analyte, Aliquot
Associations follow the aggregate graph (Case 1:1 Demographic, 1:N Diagnosis, 1:N
Sample; Sample 1:N Portion; Portion 1:N Analyte; Analyte 1:N Aliquot; Case N:1 Project).
Slides and the longitudinal clinical supplements are modelled as embedded value lists,
not first-class persistent classes, hence 8 classes vs. 14 relational tables.

Emits object/object_instances.json (the materialised object graph).  The 8 *.java
class definitions are committed alongside this script.
"""
import json, os
from _common import load_cases

HERE = os.path.dirname(__file__)


def main():
    out_dir = os.path.join(HERE, "object")
    os.makedirs(out_dir, exist_ok=True)
    cases = load_cases()
    # The object graph is the same nested aggregate as the document collection, but the
    # extents (one list per persistent class) make the per-class instance count explicit.
    extents = {k: 0 for k in ["Project", "Case", "Demographic", "Diagnosis",
                              "Sample", "Portion", "Analyte", "Aliquot"]}
    projects = set()
    for c in cases:
        pid = (c.get("project") or {}).get("project_id")
        if pid:
            projects.add(pid)
        extents["Case"] += 1
        if c.get("demographic"):
            extents["Demographic"] += 1
        extents["Diagnosis"] += len(c.get("diagnoses", []))
        for s in c.get("samples", []):
            extents["Sample"] += 1
            for p in s.get("portions", []) or []:
                extents["Portion"] += 1
                for an in p.get("analytes", []) or []:
                    extents["Analyte"] += 1
                    extents["Aliquot"] += len(an.get("aliquots", []) or [])
    extents["Project"] = len(projects)

    graph = {"classes": list(extents.keys()), "extent_sizes": extents, "objects": cases}
    json.dump(graph, open(os.path.join(out_dir, "object_instances.json"), "w",
                          encoding="utf-8"), ensure_ascii=False, indent=2)
    print("class extents:")
    for k, v in extents.items():
        print(f"  {k:14} {v:>4} objects")
    print(f"total classes: {len(extents)}")


if __name__ == "__main__":
    main()
