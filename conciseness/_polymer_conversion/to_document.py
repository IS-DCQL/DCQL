#!/usr/bin/env python3
"""Document structure for the organic-polymer data: 3 collections (Table 2).

The three consolidated English families map one-to-one to the three collections used by
the §6.4 performance run and by the §6.2 MQL / N1QL / XQuery / JSONiq / DCQL queries:

    materials_library  - polymer structure + property samples   (from polyamide.json)
    processing_logs     - injection/holding/cooling + WAXD/SAXS + mechanical (from processing.json)
    pa6t_library        - PA6T copolymer Tg-vs-density/energy curves (from pa6t.json)
"""
import json, os
HERE = os.path.dirname(__file__)
COLLECTIONS = ["materials_library", "processing_logs", "pa6t_library"]


def main():
    out_dir = os.path.join(HERE, "document")
    os.makedirs(out_dir, exist_ok=True)
    for name in COLLECTIONS:
        docs = json.load(open(os.path.join(HERE, name + "_en.json"), encoding="utf-8"))
        json.dump(docs, open(os.path.join(out_dir, name + ".json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print(f"collection {name}: {len(docs)} documents")


if __name__ == "__main__":
    main()
