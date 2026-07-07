#!/usr/bin/env python3
"""Step 1 - build the JSON documents that RumbleDB queries in the JSONiq performance run.

This mirrors the conciseness conversion pipeline (../../conciseness/_biomedical_conversion
and ../../conciseness/_polymer_conversion) but uses the FULL §6.4 performance datasets
instead of the 20-record teaching subsets, and writes the documents under ./data/ so the
benchmark can stage them where the conciseness queries expect bare relative filenames.

Outputs (./data/):
  biomedical:
      cases.json              - 1 collection: full clinical.cohort.json merged with
                                biospecimen.cohort.json by case_id (demographic{}, diagnoses[],
                                samples[] -> portions[] -> {slides[], analytes[] -> aliquots[]}).
  organic-polymer:
      materials_library.json  - polymer structure + property samples (from polyamide.json)
      processing_logs.json    - injection/holding/cooling + WAXD/SAXS + mechanical (from processing.json)
      pa6t_library.json       - PA6T copolymer Tg-vs-density/energy rows (from pa6t.json)

Raw sources live at the repository root:
      biomedical-TCGA/clinical.cohort.json, biospecimen.cohort.json
      DCQL/oql/polyamide.json, processing.json, pa6t.json
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..", "..")          # code_submission/performance/JSONiq-RumbleDB -> repo root
OUT_DIR = os.path.join(HERE, "data")

# ---- raw sources (full performance datasets) ----
TCGA = os.path.join(ROOT, "biomedical-TCGA")
CLINICAL = os.path.join(TCGA, "clinical.cohort.json")
BIOSPECIMEN = os.path.join(TCGA, "biospecimen.cohort.json")

OQL = os.path.join(ROOT, "DCQL", "oql")
POLYAMIDE = os.path.join(OQL, "polyamide.json")
PROCESSING = os.path.join(OQL, "processing.json")
PA6T = os.path.join(OQL, "pa6t.json")


# ===================== biomedical: cases.json (mirror _biomedical_conversion) =====================
def build_cases():
    """Merge the two raw GDC exports into one case-keyed nested document (Table 2, 1 collection)."""
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


# ===================== organic-polymer (mirror _polymer_conversion/translate_to_english.py) ======
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


def dump(name, docs):
    path = os.path.join(OUT_DIR, name)
    json.dump(docs, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"{name}: {len(docs)} documents -> {path}")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    # biomedical
    dump("cases.json", build_cases())
    # organic-polymer
    dump("materials_library.json", build_materials_library())
    dump("processing_logs.json", build_processing_logs())
    dump("pa6t_library.json", build_pa6t_library())


if __name__ == "__main__":
    main()
