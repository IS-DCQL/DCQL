#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Step 1 — raw data -> the form BaseX imports (§6.4 performance run).

Produces, for BOTH workloads, exactly the inputs that 2_load.sh feeds to BaseX:

  biomedical  ->  prepared_for_basex.xml   (one <json>/<_> document per merged case)
                  imported as the XML DB `tcga_cases`; the conciseness biomedical
                  XQuery queries walk it as db:open("tcga_cases")/json/_ with
                  single-underscore element names (case_id, primary_diagnosis, ...).

  organic     ->  materials_library_en.json
  polymer         processing_logs_en.json
                  pa6t_library_en.json
                  each imported as a native BaseX JSON DB of the same name; the
                  conciseness polymer XQuery queries walk them as
                  db:get("<name>")//map with <string key="..">/<number key="..">.

Conversion logic mirrors:
  conciseness/_biomedical_conversion (_common.load_cases + to_document)
  conciseness/_polymer_conversion    (translate_to_english + to_document)

Raw sources (resolved relative to this folder, repo root is ../../../):
  biomedical-TCGA/clinical.cohort.json     -> case + project + demographic + diagnoses[]
  biomedical-TCGA/biospecimen.cohort.json  -> samples[] -> portions[] -> {slides[], analytes[] -> aliquots[]}
  DCQL/oql/polyamide.json  DCQL/oql/processing.json  DCQL/oql/pa6t.json

The full TCGA cohort (clinical.cohort.json / biospecimen.cohort.json, ~50k cases) is the
§6.4 performance data; the conciseness §6.2 scripts use the *_20 teaching subset instead.
"""

import csv
import gc
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from tqdm import tqdm
except ImportError:  # tqdm is optional; degrade to a no-op iterator
    def tqdm(iterable=None, **kwargs):
        return iterable if iterable is not None else _NullBar()

    class _NullBar:
        def update(self, *_):
            pass

        def close(self):
            pass

try:
    import ijson
    IJSON_AVAILABLE = True
except ImportError:
    IJSON_AVAILABLE = False

# ===== paths =====
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent                       # -> repository root
RAW_BIOMED = ROOT / "biomedical-TCGA"
CLINICAL = RAW_BIOMED / "clinical.cohort.json"
BIOSPECIMEN = RAW_BIOMED / "biospecimen.cohort.json"
RAW_POLYMER = ROOT / "DCQL" / "oql"
POLYAMIDE = RAW_POLYMER / "polyamide.json"
PROCESSING = RAW_POLYMER / "processing.json"
PA6T = RAW_POLYMER / "pa6t.json"

# biomedical output (XML DB `tcga_cases`)
OUTPUT_XML = HERE / "prepared_for_basex.xml"

# polymer outputs (3 native JSON DBs)
POLYMER_COLLECTIONS = ["materials_library", "processing_logs", "pa6t_library"]

BATCH_SIZE = 2000


# ---------------------------------------------------------------------------
# biomedical: merge clinical + biospecimen by case_id  (mirrors _common.load_cases)
# ---------------------------------------------------------------------------
def load_cases():
    """Return a list of merged case documents, one per case_id (single-underscore keys)."""
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


# ---------------------------------------------------------------------------
# JSON -> XML in the <json>/<_> form BaseX serves and the queries expect.
# Element names are kept verbatim (single underscore), so query paths such as
# $c/case_id, $c/demographic/vital_status, $c/diagnoses/_/primary_diagnosis bind.
# ---------------------------------------------------------------------------
def to_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def build_xml(parent: ET.Element, key, value) -> None:
    elem = parent if key is None else ET.SubElement(parent, key)
    if isinstance(value, dict):
        for k, v in value.items():
            build_xml(elem, k, v)
    elif isinstance(value, list):
        for item in value:
            child = ET.SubElement(elem, "_")
            if isinstance(item, dict):
                for k, v in item.items():
                    build_xml(child, k, v)
            elif isinstance(item, list):
                for nested in item:
                    nested_child = ET.SubElement(child, "_")
                    if isinstance(nested, dict):
                        for k, v in nested.items():
                            build_xml(nested_child, k, v)
                    else:
                        nested_child.text = to_text(nested)
            else:
                child.text = to_text(item)
    else:
        elem.text = to_text(value)


def _write_batch(f_out, batch_items, pbar):
    if not batch_items:
        return
    temp_root = ET.Element("batch")
    for item in batch_items:
        row = ET.SubElement(temp_root, "_")
        if isinstance(item, dict):
            for k, v in item.items():
                build_xml(row, k, v)
        else:
            row.text = to_text(item)
        pbar.update(1)
    xml_bytes = ET.tostring(temp_root, encoding="utf-8")
    first_close = xml_bytes.find(b">")
    last_open = xml_bytes.rfind(b"<")
    if first_close != -1 and last_open != -1 and first_close < last_open:
        f_out.write(xml_bytes[first_close + 1:last_open])


def cases_to_xml(cases, output_xml: Path) -> None:
    """Stream the merged case list to <json><_>...</_></json> (constant memory)."""
    with output_xml.open("wb") as f_out:
        f_out.write(b"<json>")
        pbar = tqdm(desc="biomedical XML", unit="case")
        batch = []
        for item in cases:
            batch.append(item)
            if len(batch) >= BATCH_SIZE:
                _write_batch(f_out, batch, pbar)
                batch = []
                gc.collect()
        if batch:
            _write_batch(f_out, batch, pbar)
            gc.collect()
        pbar.close()
        f_out.write(b"</json>")


def convert_biomedical():
    if not CLINICAL.exists() or not BIOSPECIMEN.exists():
        print(f"  [skip] biomedical raw not found under {RAW_BIOMED}")
        return
    print("Biomedical: merge clinical + biospecimen by case_id ...")
    cases = load_cases()
    print(f"  merged {len(cases)} cases")
    cases_to_xml(cases, OUTPUT_XML)
    print(f"  wrote {OUTPUT_XML.name}")


# ---------------------------------------------------------------------------
# organic-polymer: translate + consolidate the 3 source files into 3 *_en.json
# collections  (mirrors _polymer_conversion/translate_to_english.py + to_document.py)
# ---------------------------------------------------------------------------
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


def convert_polymer():
    if not (POLYAMIDE.exists() and PROCESSING.exists() and PA6T.exists()):
        print(f"  [skip] polymer raw not found under {RAW_POLYMER}")
        return
    print("Organic-polymer: translate + consolidate 3 collections ...")
    builders = {
        "materials_library": build_materials_library,
        "processing_logs": build_processing_logs,
        "pa6t_library": build_pa6t_library,
    }
    for name in POLYMER_COLLECTIONS:
        docs = builders[name]()
        out = HERE / f"{name}_en.json"
        json.dump(docs, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"  {name}: {len(docs)} documents -> {out.name}")


def main():
    convert_biomedical()
    convert_polymer()
    print("Done.")


if __name__ == "__main__":
    main()
