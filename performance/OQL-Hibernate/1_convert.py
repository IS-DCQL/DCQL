#!/usr/bin/env python3
"""Step 1 — raw data -> relational CSVs.

OQL/Hibernate runs over a relational backend, so the raw datasets must first be
flattened into CSV tables. This single script covers BOTH benchmark datasets:

  * medical   (8 relational TCGA tables, streamed from the full clinical +
               biospecimen JSON dump):
               projects, demographics, cases, diagnoses,
               samples, portions, analytes, aliquots
  * material  (5 organic-polymer tables, from the polyamide / processing / pa6t
               JSON):
               materials, processing_cases, waxd_results,
               performance_results, pa6t_simulations

Run `python 2_load.py` afterwards to create the schema and import the CSVs.

The medical path streams the (large) TCGA JSON with ijson to keep memory flat.
The material path mirrors the canonical polymer relational conversion in
../../conciseness/_polymer_conversion/to_relational.py (same 5 tables, same
columns) while keeping this repo's resilient key-discovery extraction so it can
also run directly over the original polyamide / processing / pa6t JSON dumps.
"""
import csv
import json
import os
import re
import sys
from pathlib import Path

try:
    import ijson
except ImportError:
    print("Missing dependency 'ijson'. Please run: pip install ijson")
    sys.exit(1)


# =========================
# Edit the parameters here (paths)
# =========================

# medical (TCGA) raw dump
MEDICAL_JSON = Path("/home/sal/db.json")

# material (organic-polymer) raw dumps
MATERIAL_JSON = Path("/home/sal/joql/polyamide.json")
PROCESSING_JSON = Path("/home/sal/joql/processing.json")
PA6T_JSON = Path("/home/sal/joql/pa6t.json")

# shared CSV output directory consumed by 2_load.py
OUTPUT_DIR = Path("/home/sal/joql/csv_output")

# which datasets to convert: any of {"medical", "material"}
DATASETS = {"medical", "material"}

PROGRESS_WIDTH = 40

# =========================
# Usually no need to change anything below
# =========================


def safe_float(value):
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    text = text.replace(",", "")
    match = re.search(r"[-+]?\d+(\.\d+)?", text)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def safe_str(value):
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def get_first(obj, keys):
    if not isinstance(obj, dict):
        return None
    for key in keys:
        if key in obj and obj[key] not in (None, ""):
            return obj[key]
    lower_map = {str(k).lower(): k for k in obj.keys()}
    for key in keys:
        real_key = lower_map.get(str(key).lower())
        if real_key is not None and obj[real_key] not in (None, ""):
            return obj[real_key]
    return None


def normalize_key(key):
    return str(key).lower().replace("_", "").replace("-", "").replace(" ", "")


def find_value_recursive(obj, keys):
    target_keys = {normalize_key(k) for k in keys}
    if isinstance(obj, dict):
        for key, value in obj.items():
            if normalize_key(key) in target_keys and value not in (None, ""):
                return value
        for value in obj.values():
            found = find_value_recursive(value, keys)
            if found not in (None, ""):
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_value_recursive(item, keys)
            if found not in (None, ""):
                return found
    return None


def find_objects_by_key_keyword(obj, keywords):
    results = []
    keyword_set = [k.lower() for k in keywords]

    def walk(x):
        if isinstance(x, dict):
            joined_keys = " ".join(str(k).lower() for k in x.keys())
            joined_values = " ".join(
                str(v).lower()
                for v in x.values()
                if isinstance(v, (str, int, float))
            )
            full_text = joined_keys + " " + joined_values
            if any(k in full_text for k in keyword_set):
                results.append(x)
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for item in x:
                walk(item)

    walk(obj)
    return results


def detect_category(item, source_file):
    text = json.dumps(item, ensure_ascii=False).lower() + " " + source_file.lower()
    if "半芳香" in text or "semi" in text or "pa6t" in text:
        return "Semi-Aromatic"
    if "全芳香" in text or "aramid" in text or "kevlar" in text:
        return "Fully-Aromatic"
    if "脂肪" in text or "aliphatic" in text or "pa66" in text or "pa6" in text:
        return "Aliphatic"
    return None


def make_id(prefix, index):
    return f"{prefix}_{index:08d}"


class ProgressFile:
    """File wrapper for ijson that prints a read-progress bar."""

    def __init__(self, path, label, binary=True):
        self.path = Path(path)
        self.label = label
        self.binary = binary
        self.total_size = os.path.getsize(self.path)
        self.read_size = 0
        self.last_percent = -1
        mode = "rb" if binary else "r"
        if binary:
            self.file = open(self.path, mode)
        else:
            self.file = open(self.path, mode, encoding="utf-8", newline="")

    def read(self, size=-1):
        chunk = self.file.read(size)
        if chunk:
            if self.binary:
                self.read_size += len(chunk)
            else:
                self.read_size += len(chunk.encode("utf-8"))
            self.show_progress()
        return chunk

    def show_progress(self):
        if self.total_size <= 0:
            return
        percent = int(self.read_size * 100 / self.total_size)
        if percent != self.last_percent:
            self.last_percent = percent
            filled = int(PROGRESS_WIDTH * percent / 100)
            bar = "█" * filled + "-" * (PROGRESS_WIDTH - filled)
            sys.stdout.write(f"\rReading {self.label}: |{bar}| {percent:3d}%")
            sys.stdout.flush()

    def close(self):
        self.file.close()
        sys.stdout.write("\n")
        sys.stdout.flush()


def open_csv_writer(output_dir, filename, fieldnames):
    path = output_dir / filename
    f = path.open("w", newline="", encoding="utf-8")
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    return f, writer


def iter_json_items(path, label):
    """Yield top-level array items, streaming when possible, else fall back."""
    pf = ProgressFile(path, label)
    try:
        try:
            for item in ijson.items(pf, "item"):
                yield item
        except ijson.common.IncompleteJSONError:
            raise
        except Exception:
            pf.close()
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    yield item
            elif isinstance(data, dict):
                for key in ["data", "items", "records", "results"]:
                    if isinstance(data.get(key), list):
                        for item in data[key]:
                            yield item
                        return
                yield data
            return
    finally:
        try:
            pf.close()
        except Exception:
            pass


# -------------------------------------------------------------------------
# medical (TCGA) — 8 relational tables, streamed
# -------------------------------------------------------------------------

def convert_medical():
    if not MEDICAL_JSON.exists():
        print(f"Skipping medical: {MEDICAL_JSON.resolve()} not found")
        return

    print(f"\n=== medical dataset: {MEDICAL_JSON.resolve()} -> 8 relational tables ===")

    csv_files = []
    projects_f, projects_writer = open_csv_writer(
        OUTPUT_DIR, "projects.csv", ["project_id"])
    csv_files.append(projects_f)

    demographics_f, demographics_writer = open_csv_writer(
        OUTPUT_DIR, "demographics.csv",
        ["demographic_id", "case_id", "gender", "race", "ethnicity",
         "vital_status", "sex_at_birth", "age_at_index"])
    csv_files.append(demographics_f)

    cases_f, cases_writer = open_csv_writer(
        OUTPUT_DIR, "cases.csv",
        ["case_id", "primary_site", "disease_type", "submitter_id",
         "state", "project_id", "demographic_id"])
    csv_files.append(cases_f)

    diagnoses_f, diagnoses_writer = open_csv_writer(
        OUTPUT_DIR, "diagnoses.csv",
        ["diagnosis_id", "case_id", "primary_diagnosis", "vital_status",
         "age_at_diagnosis", "morphology", "classification_of_tumor",
         "tumor_grade", "tissue_or_organ_of_origin"])
    csv_files.append(diagnoses_f)

    samples_f, samples_writer = open_csv_writer(
        OUTPUT_DIR, "samples.csv",
        ["sample_id", "case_id", "sample_type", "tissue_type",
         "specimen_type", "tumor_descriptor", "preservation_method"])
    csv_files.append(samples_f)

    portions_f, portions_writer = open_csv_writer(
        OUTPUT_DIR, "portions.csv",
        ["portion_id", "sample_id", "portion_number", "is_ffpe"])
    csv_files.append(portions_f)

    analytes_f, analytes_writer = open_csv_writer(
        OUTPUT_DIR, "analytes.csv",
        ["analyte_id", "portion_id", "analyte_type", "concentration"])
    csv_files.append(analytes_f)

    aliquots_f, aliquots_writer = open_csv_writer(
        OUTPUT_DIR, "aliquots.csv",
        ["aliquot_id", "analyte_id", "submitter_id", "state",
         "concentration", "aliquot_quantity", "aliquot_volume"])
    csv_files.append(aliquots_f)

    seen_projects = set()
    counts = {k: 0 for k in [
        "cases", "projects", "demographics", "diagnoses",
        "samples", "portions", "analytes", "aliquots"]}

    pf = ProgressFile(MEDICAL_JSON, "db.json")
    try:
        for case in ijson.items(pf, "item"):
            case_id = case.get("case_id")
            if not case_id:
                continue

            project = case.get("project") or {}
            project_id = project.get("project_id")
            demographic = case.get("demographic") or {}
            demographic_id = demographic.get("demographic_id")

            if project_id and project_id not in seen_projects:
                projects_writer.writerow({"project_id": project_id})
                seen_projects.add(project_id)
                counts["projects"] += 1

            if demographic_id:
                demographics_writer.writerow({
                    "demographic_id": demographic_id,
                    "case_id": case_id,
                    "gender": demographic.get("gender"),
                    "race": demographic.get("race"),
                    "ethnicity": demographic.get("ethnicity"),
                    "vital_status": demographic.get("vital_status"),
                    "sex_at_birth": demographic.get("sex_at_birth"),
                    "age_at_index": demographic.get("age_at_index"),
                })
                counts["demographics"] += 1

            cases_writer.writerow({
                "case_id": case_id,
                "primary_site": case.get("primary_site"),
                "disease_type": case.get("disease_type"),
                "submitter_id": case.get("submitter_id"),
                "state": case.get("state"),
                "project_id": project_id,
                "demographic_id": demographic_id,
            })
            counts["cases"] += 1

            for diagnosis in case.get("diagnoses") or []:
                diagnosis_id = diagnosis.get("diagnosis_id")
                if not diagnosis_id:
                    continue
                diagnoses_writer.writerow({
                    "diagnosis_id": diagnosis_id,
                    "case_id": case_id,
                    "primary_diagnosis": diagnosis.get("primary_diagnosis"),
                    "vital_status": diagnosis.get("vital_status"),
                    "age_at_diagnosis": diagnosis.get("age_at_diagnosis"),
                    "morphology": diagnosis.get("morphology"),
                    "classification_of_tumor": diagnosis.get("classification_of_tumor"),
                    "tumor_grade": diagnosis.get("tumor_grade"),
                    "tissue_or_organ_of_origin": diagnosis.get("tissue_or_organ_of_origin"),
                })
                counts["diagnoses"] += 1

            for sample in case.get("samples") or []:
                sample_id = sample.get("sample_id")
                if not sample_id:
                    continue
                samples_writer.writerow({
                    "sample_id": sample_id,
                    "case_id": case_id,
                    "sample_type": sample.get("sample_type"),
                    "tissue_type": sample.get("tissue_type"),
                    "specimen_type": sample.get("specimen_type"),
                    "tumor_descriptor": sample.get("tumor_descriptor"),
                    "preservation_method": sample.get("preservation_method"),
                })
                counts["samples"] += 1

                for portion in sample.get("portions") or []:
                    portion_id = portion.get("portion_id")
                    if not portion_id:
                        continue
                    portions_writer.writerow({
                        "portion_id": portion_id,
                        "sample_id": sample_id,
                        "portion_number": portion.get("portion_number"),
                        "is_ffpe": portion.get("is_ffpe"),
                    })
                    counts["portions"] += 1

                    for analyte in portion.get("analytes") or []:
                        analyte_id = analyte.get("analyte_id")
                        if not analyte_id:
                            continue
                        analytes_writer.writerow({
                            "analyte_id": analyte_id,
                            "portion_id": portion_id,
                            "analyte_type": analyte.get("analyte_type"),
                            "concentration": safe_float(analyte.get("concentration")),
                        })
                        counts["analytes"] += 1

                        for aliquot in analyte.get("aliquots") or []:
                            aliquot_id = aliquot.get("aliquot_id")
                            if not aliquot_id:
                                continue
                            aliquots_writer.writerow({
                                "aliquot_id": aliquot_id,
                                "analyte_id": analyte_id,
                                "submitter_id": aliquot.get("submitter_id"),
                                "state": aliquot.get("state"),
                                "concentration": safe_float(aliquot.get("concentration")),
                                "aliquot_quantity": safe_float(aliquot.get("aliquot_quantity")),
                                "aliquot_volume": safe_float(aliquot.get("aliquot_volume")),
                            })
                            counts["aliquots"] += 1

            if counts["cases"] % 1000 == 0:
                for f in csv_files:
                    f.flush()
    finally:
        pf.close()
        for f in csv_files:
            f.close()

    print("medical conversion complete:")
    for k in ["cases", "projects", "demographics", "diagnoses",
              "samples", "portions", "analytes", "aliquots"]:
        print(f"  {k:13s} {counts[k]}")


# -------------------------------------------------------------------------
# material (organic-polymer) — 5 relational tables
# -------------------------------------------------------------------------

def parse_materials(writer):
    count = 0
    if not MATERIAL_JSON.exists():
        print(f"Skipping: {MATERIAL_JSON} not found")
        return count
    print(f"\nProcessing the base material property library: {MATERIAL_JSON}")
    for index, item in enumerate(iter_json_items(MATERIAL_JSON, "polyamide.json"), start=1):
        if not isinstance(item, dict):
            continue
        material_id = get_first(item, [
            "material_id", "id", "_id", "pid", "PID", "编号", "聚合物编号"
        ]) or make_id("mat", index)
        name = find_value_recursive(item, [
            "name", "Name", "化学名称", "名称", "material_name", "polymer_name"])
        smiles = find_value_recursive(item, [
            "smiles", "SMILES", "repeatUnitSmiles", "repeat_unit_smiles",
            "重复单元SMILES", "化学结构"])
        repeat_unit_smiles = find_value_recursive(item, [
            "repeatUnitSmiles", "repeat_unit_smiles", "重复单元SMILES"])
        pid = find_value_recursive(item, ["pid", "PID", "polymer_id", "聚合物编号"])
        category = find_value_recursive(item, [
            "category", "类别", "类型", "material_type", "polyamide_type"
        ]) or detect_category(item, MATERIAL_JSON.name)
        writer.writerow({
            "material_id": safe_str(material_id),
            "name": safe_str(name),
            "smiles": safe_str(smiles),
            "repeat_unit_smiles": safe_str(repeat_unit_smiles),
            "pid": safe_str(pid),
            "category": safe_str(category),
            "average_mw": safe_float(find_value_recursive(item, [
                "averageMW", "average_mw", "Mn", "Mw", "分子量", "数均分子量"])),
            "tensile_modulus": safe_float(find_value_recursive(item, [
                "tensileModulus", "tensile_modulus", "拉伸模量"])),
            "tensile_strength": safe_float(find_value_recursive(item, [
                "tensileStrength", "tensile_strength", "拉伸强度"])),
            "thermal_decomposition": safe_float(find_value_recursive(item, [
                "thermalDecomposition", "thermal_decomposition", "热分解温度"])),
            "glass_temperature": safe_float(find_value_recursive(item, [
                "glassTemperature", "glass_temperature", "Tg", "玻璃化转变温度"])),
            "melting_temperature": safe_float(find_value_recursive(item, [
                "meltingTemperature", "melting_temperature", "Tm", "熔点", "熔融温度"])),
            "heat_deflection_temperature": safe_float(find_value_recursive(item, [
                "heatDeflectionTemperature", "heat_deflection_temperature", "HDT", "热变形温度"])),
            "raw_source": MATERIAL_JSON.name,
        })
        count += 1
    return count


def parse_processing(processing_writer, waxd_writer, performance_writer):
    counts = {"processing_cases": 0, "waxd_results": 0, "performance_results": 0}
    if not PROCESSING_JSON.exists():
        print(f"Skipping: {PROCESSING_JSON} not found")
        return counts
    print(f"\nProcessing the processing-structure-performance data: {PROCESSING_JSON}")
    for index, item in enumerate(iter_json_items(PROCESSING_JSON, "processing.json"), start=1):
        if not isinstance(item, dict):
            continue
        process_id = get_first(item, [
            "process_id", "processing_id", "id", "_id", "编号", "实验编号"
        ]) or make_id("proc", index)
        sample_no = find_value_recursive(item, [
            "sample_no", "sampleNo", "sample_id", "样品编号", "牌号", "number"])
        material_name = find_value_recursive(item, [
            "material_name", "material", "polymer", "name", "材料名称", "树脂名称"])
        material_id = find_value_recursive(item, [
            "material_id", "pid", "PID", "聚合物编号"])
        formulation = find_value_recursive(item, [
            "formulation", "composition", "配方", "组成", "配比"])

        processing_writer.writerow({
            "process_id": safe_str(process_id),
            "material_name": safe_str(material_name),
            "material_id": safe_str(material_id),
            "sample_no": safe_str(sample_no),
            "formulation": safe_str(formulation),
            "speed": safe_float(find_value_recursive(item, [
                "speed", "注射速度", "射出速度"])),
            "pressure": safe_float(find_value_recursive(item, [
                "pressure", "保压压力", "压力"])),
            "pressure_time": safe_float(find_value_recursive(item, [
                "pressure_time", "holding_time", "保压时间"])),
            "cooling_temperature": safe_float(find_value_recursive(item, [
                "cooling_temperature", "mold_temperature", "冷却温度", "模具温度"])),
            "cooling_time": safe_float(find_value_recursive(item, [
                "cooling_time", "冷却时间"])),
            "injection_rate": safe_float(find_value_recursive(item, [
                "injection_rate", "injectionRate", "注射速率", "注射速度", "speed"])),
            "processing_temperature": safe_float(find_value_recursive(item, [
                "processing_temperature", "processingTemperature", "加工温度", "熔体温度"])),
            "raw_source": PROCESSING_JSON.name,
        })
        counts["processing_cases"] += 1

        waxd_objects = find_objects_by_key_keyword(item, [
            "waxd", "wide-angle", "x-ray", "结晶", "晶粒", "衍射"])
        if not waxd_objects:
            waxd_objects = [item]

        written_waxd = False
        for waxd_index, waxd in enumerate(waxd_objects, start=1):
            quality_value = find_value_recursive(waxd, [
                "quality_value", "qualityValue", "value", "数值", "质量数值", "结晶度"])
            crystallinity = find_value_recursive(waxd, ["crystallinity", "结晶度"])
            if quality_value is None and crystallinity is None and not written_waxd:
                quality_value = find_value_recursive(item, [
                    "quality_value", "qualityValue", "value", "数值", "质量数值"])
            if quality_value is None and crystallinity is None:
                continue
            waxd_writer.writerow({
                "waxd_id": f"{process_id}_waxd_{waxd_index}",
                "process_id": safe_str(process_id),
                "sample_no": safe_str(sample_no),
                "pa_content": safe_float(find_value_recursive(waxd, [
                    "PA6T含量", "pa6t_content", "PA6T_content", "含量"])),
                "waxd_peak": safe_str(find_value_recursive(waxd, [
                    "waxd_peak", "peak", "峰", "衍射峰"])),
                "crystallinity": safe_float(crystallinity),
                "crystal_size": safe_float(find_value_recursive(waxd, [
                    "crystal_size", "晶粒尺寸"])),
                "orientation": safe_float(find_value_recursive(waxd, [
                    "orientation", "取向度", "取向"])),
                "quality_value": safe_float(quality_value),
                "raw_value": safe_str(quality_value),
            })
            counts["waxd_results"] += 1
            written_waxd = True

        performance_writer.writerow({
            "performance_id": f"{process_id}_perf",
            "process_id": safe_str(process_id),
            "sample_no": safe_str(sample_no),
            "tensile_strength": safe_float(find_value_recursive(item, [
                "tensileStrength", "tensile_strength", "拉伸强度"])),
            "tensile_modulus": safe_float(find_value_recursive(item, [
                "tensileModulus", "tensile_modulus", "拉伸模量"])),
            "elongation": safe_float(find_value_recursive(item, [
                "elongation", "断裂伸长率", "伸长率"])),
            "impact_strength": safe_float(find_value_recursive(item, [
                "impactStrength", "impact_strength", "冲击强度"])),
            "composite_mechanical_property": safe_float(find_value_recursive(item, [
                "compositeMechanicalProperty", "复合材料力学性能", "力学性能"])),
            "raw_source": PROCESSING_JSON.name,
        })
        counts["performance_results"] += 1
    return counts


def parse_pa6t(writer):
    count = 0
    if not PA6T_JSON.exists():
        print(f"Skipping: {PA6T_JSON} not found")
        return count
    print(f"\nProcessing the PA6T micromechanics data: {PA6T_JSON}")
    for index, item in enumerate(iter_json_items(PA6T_JSON, "pa6t.json"), start=1):
        if not isinstance(item, dict):
            continue
        simulation_id = get_first(item, [
            "simulation_id", "id", "_id", "编号", "实验编号"
        ]) or make_id("sim", index)
        writer.writerow({
            "simulation_id": safe_str(simulation_id),
            "pa6t_content": safe_float(find_value_recursive(item, [
                "pa6t_content", "PA6T含量", "PA6T_content", "含量"])),
            "temperature": safe_float(find_value_recursive(item, [
                "temperature", "Temperature", "温度", "T"])),
            "density": safe_float(find_value_recursive(item, [
                "density", "Density", "密度"])),
            "energy": safe_float(find_value_recursive(item, [
                "energy", "Energy", "能量"])),
            "transition_temperature": safe_float(find_value_recursive(item, [
                "transition_temperature", "Tg", "玻璃化转变温度", "转变温度"])),
            "raw_source": PA6T_JSON.name,
        })
        count += 1
    return count


def convert_material():
    print("\n=== material dataset -> 5 relational tables ===")

    csv_files = []
    materials_f, materials_writer = open_csv_writer(
        OUTPUT_DIR, "materials.csv",
        ["material_id", "name", "smiles", "repeat_unit_smiles", "pid",
         "category", "average_mw", "tensile_modulus", "tensile_strength",
         "thermal_decomposition", "glass_temperature", "melting_temperature",
         "heat_deflection_temperature", "raw_source"])
    csv_files.append(materials_f)

    processing_f, processing_writer = open_csv_writer(
        OUTPUT_DIR, "processing_cases.csv",
        ["process_id", "material_name", "material_id", "sample_no",
         "formulation", "speed", "pressure", "pressure_time",
         "cooling_temperature", "cooling_time", "injection_rate",
         "processing_temperature", "raw_source"])
    csv_files.append(processing_f)

    waxd_f, waxd_writer = open_csv_writer(
        OUTPUT_DIR, "waxd_results.csv",
        ["waxd_id", "process_id", "sample_no", "pa_content", "waxd_peak",
         "crystallinity", "crystal_size", "orientation", "quality_value",
         "raw_value"])
    csv_files.append(waxd_f)

    performance_f, performance_writer = open_csv_writer(
        OUTPUT_DIR, "performance_results.csv",
        ["performance_id", "process_id", "sample_no", "tensile_strength",
         "tensile_modulus", "elongation", "impact_strength",
         "composite_mechanical_property", "raw_source"])
    csv_files.append(performance_f)

    pa6t_f, pa6t_writer = open_csv_writer(
        OUTPUT_DIR, "pa6t_simulations.csv",
        ["simulation_id", "pa6t_content", "temperature", "density",
         "energy", "transition_temperature", "raw_source"])
    csv_files.append(pa6t_f)

    try:
        material_count = parse_materials(materials_writer)
        processing_counts = parse_processing(
            processing_writer, waxd_writer, performance_writer)
        pa6t_count = parse_pa6t(pa6t_writer)
    finally:
        for f in csv_files:
            f.close()

    print("material conversion complete:")
    print(f"  materials           {material_count}")
    print(f"  processing_cases    {processing_counts['processing_cases']}")
    print(f"  waxd_results        {processing_counts['waxd_results']}")
    print(f"  performance_results {processing_counts['performance_results']}")
    print(f"  pa6t_simulations    {pa6t_count}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR.resolve()}")
    print(f"Datasets to convert: {', '.join(sorted(DATASETS))}")

    if "medical" in DATASETS:
        convert_medical()
    if "material" in DATASETS:
        convert_material()

    print("\nAll conversions complete. Next, run: python 2_load.py")


if __name__ == "__main__":
    main()
