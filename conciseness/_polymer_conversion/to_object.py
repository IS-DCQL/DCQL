#!/usr/bin/env python3
"""Object structure for the organic-polymer data: 5 persistent classes (Table 2).

The §6.4 performance run accessed polymer data through Hibernate over the 5 `public`
tables (raw SQL, no hand-written polymer JPA entities). For the object model we expose
those 5 storage units as 5 persistent classes, one per table:

    Material, ProcessingCase, WaxdResult, PerformanceResult, Pa6tSimulation

Emits object/object_instances.json (extent sizes + materialised graph). The 5 *.java
class definitions are committed alongside this script.
"""
import json, os
HERE = os.path.dirname(__file__)
CLASSES = ["Material", "ProcessingCase", "WaxdResult", "PerformanceResult", "Pa6tSimulation"]


def main():
    out_dir = os.path.join(HERE, "object")
    os.makedirs(out_dir, exist_ok=True)
    materials = json.load(open(os.path.join(HERE, "materials_library_en.json"), encoding="utf-8"))
    processing = json.load(open(os.path.join(HERE, "processing_logs_en.json"), encoding="utf-8"))
    pa6t = json.load(open(os.path.join(HERE, "pa6t_library_en.json"), encoding="utf-8"))
    ext = {"Material": len(materials), "ProcessingCase": len(processing),
           "WaxdResult": sum(1 for p in processing if p.get("WAXD_result")),
           "PerformanceResult": sum(1 for p in processing if p.get("mechanical")),
           "Pa6tSimulation": len(pa6t)}
    graph = {"classes": CLASSES, "extent_sizes": ext,
             "objects": {"materials_library": materials, "processing_logs": processing,
                         "pa6t_library": pa6t}}
    json.dump(graph, open(os.path.join(out_dir, "object_instances.json"), "w",
                          encoding="utf-8"), ensure_ascii=False, indent=2)
    print("class extents:")
    for c in CLASSES:
        print(f"  {c:18} {ext[c]:>6} objects")
    print(f"total classes: {len(CLASSES)}")


if __name__ == "__main__":
    main()
