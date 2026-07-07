#!/usr/bin/env python3
"""DCQL (NMDMS) — data conversion.

Produces the document structures the NMDMS read path ingests, mirroring the conciseness
converters but on the full §6.4 cohort:
  biomedical      : merge clinical.cohort.json + biospecimen.cohort.json by case_id
                    -> 1 collection `cases`
  organic-polymer : polyamide.json / processing.json / pa6t.json
                    -> 3 collections materials_library / processing_logs / pa6t_library

Output: ./document/<domain>/<collection>.json  (consumed by 2_load.py)
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
TCGA = os.path.join(ROOT, "biomedical-TCGA")
OQL = os.path.join(ROOT, "DCQL", "oql")
OUT = os.path.join(HERE, "document")

# full-cohort sources by default; override with the _20 teaching files for a smoke test
CLINICAL = os.environ.get("CLINICAL_JSON", os.path.join(TCGA, "clinical.cohort.json"))
BIOSPEC = os.environ.get("BIOSPECIMEN_JSON", os.path.join(TCGA, "biospecimen.cohort.json"))

CATEGORY_MAP = {"半芳香族": "Semi-Aromatic", "全芳香族": "Fully-Aromatic", "脂肪族": "Aliphatic"}


def num(v):
    if v is None or isinstance(v, (int, float)):
        return v
    s = str(v).strip().replace("\t", "")
    m = re.search(r"-?\d+\.?\d*", s)
    return float(m.group()) if m else None


def first(x):
    return x[0] if isinstance(x, list) and x else None


def biomedical():
    clinical = json.load(open(CLINICAL, encoding="utf-8"))
    biospec = json.load(open(BIOSPEC, encoding="utf-8"))
    by_id = {}
    for c in clinical:
        by_id[c["case_id"]] = {**c, "samples": []}
    for b in biospec:
        by_id.setdefault(b["case_id"], {"case_id": b["case_id"]})["samples"] = b.get("samples", []) or []
    return list(by_id.values())


def materials_library():
    out = []
    for rec in json.load(open(os.path.join(OQL, "polyamide.json"), encoding="utf-8")):
        c = rec["content"]
        samples = [{
            "thermal": {"glass_temperature": num((first(s.get("glassTemperature", [])) or {}).get("value")),
                        "melting_temperature": num((first(s.get("meltingPoint", [])) or {}).get("value")),
                        "thermal_decomposition": num((first(s.get("thermalDecomposition", [])) or {}).get("value"))},
            "mechanical": {"tensile_strength": num((first(s.get("tensileStrength", [])) or {}).get("value")),
                           "tensile_modulus": num((first(s.get("tensileModulus", [])) or {}).get("value"))},
        } for s in c.get("sample", []) or []]
        out.append({"meta": {"data_id": (rec.get("meta") or {}).get("数据ID")},
                    "basic_info": {"pid": c.get("pid"),
                                   "name": first(c.get("name", [])) if isinstance(c.get("name"), list) else c.get("name"),
                                   "category": CATEGORY_MAP.get(c.get("category"), c.get("category")),
                                   "smiles": first(c.get("smiles", []))},
                    "samples": samples})
    return out


def processing_logs():
    out = []
    for rec in json.load(open(os.path.join(OQL, "processing.json"), encoding="utf-8")):
        c = rec["content"]
        inj = c.get("注射段", {}) or {}
        out.append({"meta": {"data_id": (rec.get("meta") or {}).get("数据ID")},
                    "material_name": c.get("材料名称"),
                    "machine_settings": {"injection": {"stages": [num(v) for v in inj.values()]}},
                    "WAXD_result": {"alpha_crystallinity": num((c.get("WAXD结果", {}) or {}).get("α晶结晶度（%）"))},
                    "mechanical": {"tensile_strength": num((c.get("共聚物力学性能", {}) or {}).get("拉伸强度（MPa）"))}})
    return out


def pa6t_library():
    return [{"composition_variation": {"copolymer": r.get("PA6T共聚物"), "pa6t_content": num(r.get("PA6T含量"))},
             "temperature": num(r.get("温度")), "density": num(r.get("密度")), "energy": num(r.get("能量"))}
            for r in json.load(open(os.path.join(OQL, "pa6t.json"), encoding="utf-8"))]


def dump(domain, name, docs):
    d = os.path.join(OUT, domain)
    os.makedirs(d, exist_ok=True)
    json.dump(docs, open(os.path.join(d, name + ".json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(f"{domain}/{name}: {len(docs)} documents")


def main():
    dump("biomedical", "cases", biomedical())
    dump("organic-polymer", "materials_library", materials_library())
    dump("organic-polymer", "processing_logs", processing_logs())
    dump("organic-polymer", "pa6t_library", pa6t_library())


if __name__ == "__main__":
    main()
