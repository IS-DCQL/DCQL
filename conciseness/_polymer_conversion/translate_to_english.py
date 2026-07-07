#!/usr/bin/env python3
"""Translate + consolidate the organic-polymer data EXACTLY as the §6.4 performance run did.

The performance experiment selected **three** prepared files (not the full NMDMS dump):

    DCQL/oql/polyamide.json   (1093 polymer-structure records: fully aromatic + semi-aromatic + aliphatic, with category)
    DCQL/oql/processing.json     (128 injection/holding/cooling + WAXD/SAXS + mechanical records)
    DCQL/oql/pa6t.json     (~31.9k PA6T-copolymer Tg-vs-density/energy simulation rows, pre-flattened)

These map one-to-one to the three document collections of Table 2
(materials_library / processing_logs / pa6t_library). This script reads them, translates
the attribute keys to English, and writes the three consolidated English collection files
(which ARE the document structure); to_relational.py / to_object.py derive the 5 tables /
5 classes from them. Chemical entity names / SMILES / categorical values are kept verbatim.
"""
import json, os, re

HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, "..", "..", "..", "DCQL", "oql")
POLYAMIDE = os.path.join(SRC, "polyamide.json")
PROCESSING = os.path.join(SRC, "processing.json")
PA6T = os.path.join(SRC, "pa6t.json")


def num(v):
    if v is None or isinstance(v, (int, float)):
        return v
    s = str(v).strip().replace("\t", "")
    m = re.search(r"-?\d+\.?\d*", s)
    return float(m.group()) if m else None


def first(lst):
    return lst[0] if isinstance(lst, list) and lst else None


CATEGORY_MAP = {"半芳香族": "Semi-Aromatic", "全芳香族": "Fully-Aromatic", "脂肪族": "Aliphatic"}


def category_en(v):
    return CATEGORY_MAP.get(v, v)


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
                "category": category_en(c.get("category")),
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


def main():
    coll = {"materials_library": build_materials_library(),
            "processing_logs": build_processing_logs(),
            "pa6t_library": build_pa6t_library()}
    for name, docs in coll.items():
        json.dump(docs, open(os.path.join(HERE, name + "_en.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"{name}: {len(docs)} records")


if __name__ == "__main__":
    main()
