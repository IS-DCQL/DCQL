#!/usr/bin/env python3
"""Document structure for the biomedical data: 1 collection (Table 2).

Aggregate-storage strategy: the whole patient record is a single nested document, so
the clinical and biospecimen exports collapse into ONE collection `cases`. Each document
nests demographic{}, diagnoses[], and samples[] -> portions[] -> {slides[], analytes[]
-> aliquots[]}.  This is the shared collection queried by MQL / N1QL / XQuery / JSONiq /
DCQL in ../<language>/biomedical/.
"""
import json, os
from _common import load_cases

HERE = os.path.dirname(__file__)


def main():
    out_dir = os.path.join(HERE, "document")
    os.makedirs(out_dir, exist_ok=True)
    cases = load_cases()
    json.dump(cases, open(os.path.join(out_dir, "cases.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"collection cases: {len(cases)} documents")


if __name__ == "__main__":
    main()
