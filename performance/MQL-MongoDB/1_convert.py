#!/usr/bin/env python3
"""Step 1 -- raw data -> MongoDB document structure (conversion step).

MongoDB uses aggregate document storage, so each logical record collapses into a single
nested document. This script writes the JSON collection files that 2_load.py imports.

It mirrors the conversion logic of the §6.2 teaching scripts in
    ../../conciseness/_biomedical_conversion/{_common,to_document}.py
    ../../conciseness/_polymer_conversion/{translate_to_english,to_document}.py
but reads the FULL §6.4 performance cohort (clinical.cohort.json / biospecimen.cohort.json
and the full polyamide/processing/pa6t json), not the _20 teaching subset.

Output (written into ./document/<domain>/):
    biomedical:       cases.json                 (1 collection -- merged patient docs)
    organic-polymer:  materials_library.json,
                      processing_logs.json,
                      pa6t_library.json          (3 collections)

Raw source paths are overridable via environment variables (see CONFIG below).
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

# ========== CONFIG (override via env) ==========
# Biomedical TCGA raw exports (full cohort).
BIO_RAW = os.environ.get(
    "BIO_RAW_DIR",
    os.path.join(HERE, "..", "..", "..", "biomedical-TCGA"),
)
CLINICAL = os.environ.get("CLINICAL_JSON", os.path.join(BIO_RAW, "clinical.cohort.json"))
BIOSPECIMEN = os.environ.get("BIOSPECIMEN_JSON", os.path.join(BIO_RAW, "biospecimen.cohort.json"))

# Organic-polymer raw exports (full files).
POLY_RAW = os.environ.get(
    "POLY_RAW_DIR",
    os.path.join(HERE, "..", "..", "..", "DCQL", "oql"),
)
POLYAMIDE = os.environ.get("POLYAMIDE_JSON", os.path.join(POLY_RAW, "polyamide.json"))
PROCESSING = os.environ.get("PROCESSING_JSON", os.path.join(POLY_RAW, "processing.json"))
PA6T = os.environ.get("PA6T_JSON", os.path.join(POLY_RAW, "pa6t.json"))

OUT_DIR = os.environ.get("CONVERT_OUT_DIR", os.path.join(HERE, "document"))
# ===============================================


# ---------- biomedical (mirrors _biomedical_conversion/_common.py) ----------
def load_cases():
    """Merge the clinical + biospecimen exports into one nested doc per case_id."""
    clinical = json.load(open(CLINICAL, encoding="utf-8"))
    biospec = json.load(open(BIOSPECIMEN, encoding="utf-8"))
    by_id = {}
    for c in clinical:
        cid = c["case_id"]
        by_id[cid] = {
            "case_id": cid,
            "project": c.get("project", {}),
            "primary_site": c.get("primary_site"),
            "disease_type": c.get("disease_type"),
            "submitter_id": c.get("submitter_id"),
            "state": c.get("state"),
            "created_datetime": c.get("created_datetime"),
            "updated_datetime": c.get("updated_datetime"),
            "demographic": c.get("demographic", {}) or {},
            "diagnoses": c.get("diagnoses", []) or [],
            "samples": [],
        }
    for b in biospec:
        cid = b["case_id"]
        rec = by_id.setdefault(cid, {"case_id": cid, "project": b.get("project", {}),
                                     "demographic": {}, "diagnoses": [], "samples": []})
        rec["samples"] = b.get("samples", []) or []
    return list(by_id.values())


# ---------- organic-polymer (mirrors _polymer_conversion/translate_to_english.py) ----------
def num(v):
    if v is None or isinstance(v, (int, float)):
        return v
    s = str(v).strip().replace("\t", "")
    m = re.search(r"-?\d+\.?\d*", s)
    return float(m.group()) if m else None


def first(lst):
    return lst[0] if isinstance(lst, list) and lst else None


def build_materials_library():
    out = []
    for rec in json.load(open(POLYAMIDE, encoding="utf-8")):
        c = rec["content"]
        samples = []
        for s in c.get("sample", []) or []:
            samples.append({
                "average_mw": num((first(s.get("averageMW", {}).get("mw", [])) or {}).get("value")) if isinstance(s.get("averageMW"), dict) else None,
                "thermal": {
                    "glass_temperature": num((first(s.get("glassTemperature", [])) or {}).get("value")),
                    "melting_temperature": num((first(s.get("meltingPoint", [])) or {}).get("value")),
                    "thermal_decomposition": num((first(s.get("thermalDecomposition", [])) or {}).get("value")),
                },
                "mechanical": {
                    "tensile_strength": num((first(s.get("tensileStrength", [])) or {}).get("value")),
                    "tensile_modulus": num((first(s.get("tensileModulus", [])) or {}).get("value")),
                    "elongation_at_break": num((first(s.get("elongationAtBreak", [])) or {}).get("value")),
                },
            })
        out.append({
            "doc_id": rec.get("doc_id"),
            "meta": {"data_id": (rec.get("meta") or {}).get("数据ID")},
            "basic_info": {
                "pid": c.get("pid"),
                "name": first(c.get("name", [])) if isinstance(c.get("name"), list) else c.get("name"),
                "category": {"半芳香族": "Semi-Aromatic", "全芳香族": "Fully-Aromatic", "脂肪族": "Aliphatic"}.get(c.get("category"), c.get("category")),
                "smiles": first(c.get("smiles", [])),
                "repeat_unit_smiles": first(c.get("repeatUnitSmiles", [])),
                "reactive_group": first(c.get("reactiveGroup", [])),
            },
            "samples": samples,
        })
    return out


def build_processing_logs():
    out = []
    for rec in json.load(open(PROCESSING, encoding="utf-8")):
        c = rec["content"]
        inj, hold, cool = c.get("注射段", {}) or {}, c.get("保压段", {}) or {}, c.get("冷却段", {}) or {}
        waxd, saxs, mech = c.get("WAXD结果", {}) or {}, c.get("SAXS结果", {}) or {}, c.get("共聚物力学性能", {}) or {}
        out.append({
            "meta": {"data_id": (rec.get("meta") or {}).get("数据ID")},
            "material_name": c.get("材料名称"),
            "machine_settings": {
                "injection": {"stages": [num(v) for v in inj.values()]},
                "holding": {"pressures": [num(v) for k, v in hold.items() if "MPa" in k],
                            "times": [num(v) for k, v in hold.items() if "时间" in k]},
                "cooling": {"mold_temperature": num(cool.get("模具温度（℃）")),
                            "cooling_time": num(cool.get("冷却时间（s）"))},
            },
            "WAXD_result": {"alpha_crystallinity": num(waxd.get("α晶结晶度（%）")),
                            "alpha_100": num(waxd.get("α(100)结晶度（%）")),
                            "gamma": num(waxd.get("γ(100/010/110)结晶度（%）"))},
            "SAXS_result": {"lamellar_thickness": num(saxs.get("片晶厚度（nm）")),
                            "long_period": num(saxs.get("长周期（nm）")),
                            "orientation_index": num(saxs.get("取向指数"))},
            "mechanical": {"tensile_strength": num(mech.get("拉伸强度（MPa）")),
                           "yield_stress": num(mech.get("屈服应力（MPa）")),
                           "elongation_at_break": num(mech.get("断裂伸长率（%）")),
                           "elastic_modulus": num(mech.get("弹性模量（MPa）"))},
        })
    return out


def build_pa6t_library():
    out = []
    for rec in json.load(open(PA6T, encoding="utf-8")):
        out.append({
            "doc_id": rec.get("doc_id"),
            "composition_variation": {"copolymer": rec.get("PA6T共聚物"),
                                      "pa6t_content": num(rec.get("PA6T含量"))},
            "temperature": num(rec.get("温度")),
            "density": num(rec.get("密度")),
            "energy": num(rec.get("能量")),
            "temperature_range": {"lb": num(rec.get("温度范围_lb")), "ub": num(rec.get("温度范围_ub"))},
        })
    return out


def dump(domain, name, docs):
    out_dir = os.path.join(OUT_DIR, domain)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, name + ".json")
    json.dump(docs, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"  collection {name}: {len(docs)} documents -> {path}")


def main():
    print("== biomedical (1 collection) ==")
    dump("biomedical", "cases", load_cases())

    print("== organic-polymer (3 collections) ==")
    dump("organic-polymer", "materials_library", build_materials_library())
    dump("organic-polymer", "processing_logs", build_processing_logs())
    dump("organic-polymer", "pa6t_library", build_pa6t_library())

    print("\nConversion finished. Run 2_load.py next.")


if __name__ == "__main__":
    main()
