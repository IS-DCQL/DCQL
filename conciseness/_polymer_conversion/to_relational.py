#!/usr/bin/env python3
"""Relational structure for the organic-polymer data: 5 tables (Table 2).

Reproduces the as-run §6.4 performance schema (schema `public`, see
`DCQL/oql/csv_output/`). The model is intentionally denormalised (e.g. `materials`
carries the property columns directly), matching how the performance run loaded it.
Table & column names match the SQL/OQL §6.2 polymer queries:

    materials, processing_cases, waxd_results, performance_results, pa6t_simulations
"""
import csv, json, os
HERE = os.path.dirname(__file__)

COLUMNS = {
    "materials": ["material_id", "name", "smiles", "repeat_unit_smiles", "pid", "category",
                  "average_mw", "tensile_modulus", "tensile_strength", "thermal_decomposition",
                  "glass_temperature", "melting_temperature", "heat_deflection_temperature",
                  "raw_source"],
    "processing_cases": ["process_id", "material_name", "material_id", "sample_no",
                         "formulation", "speed", "pressure", "pressure_time",
                         "cooling_temperature", "cooling_time", "injection_rate",
                         "processing_temperature", "raw_source"],
    "waxd_results": ["waxd_id", "process_id", "sample_no", "pa_content", "waxd_peak",
                     "crystallinity", "crystal_size", "orientation", "quality_value",
                     "raw_value"],
    "performance_results": ["performance_id", "process_id", "sample_no", "tensile_strength",
                            "tensile_modulus", "elongation", "impact_strength",
                            "composite_mechanical_property", "raw_source"],
    "pa6t_simulations": ["simulation_id", "pa6t_content", "temperature", "density", "energy",
                         "transition_temperature", "raw_source"],
}


def main():
    out_dir = os.path.join(HERE, "relational")
    os.makedirs(out_dir, exist_ok=True)
    rows = {t: [] for t in COLUMNS}

    materials = json.load(open(os.path.join(HERE, "materials_library_en.json"), encoding="utf-8"))
    processing = json.load(open(os.path.join(HERE, "processing_logs_en.json"), encoding="utf-8"))
    pa6t = json.load(open(os.path.join(HERE, "pa6t_library_en.json"), encoding="utf-8"))

    for i, m in enumerate(materials, 1):
        mid = f"PM{i:05d}"
        bi, s0 = m["basic_info"], (m["samples"][0] if m["samples"] else {})
        th, mech = s0.get("thermal", {}), s0.get("mechanical", {})
        rows["materials"].append({
            "material_id": mid, "name": bi.get("name"), "smiles": bi.get("smiles"),
            "repeat_unit_smiles": bi.get("repeat_unit_smiles"), "pid": bi.get("pid"),
            "category": bi.get("category"), "average_mw": s0.get("average_mw"),
            "tensile_modulus": mech.get("tensile_modulus"),
            "tensile_strength": mech.get("tensile_strength"),
            "thermal_decomposition": th.get("thermal_decomposition"),
            "glass_temperature": th.get("glass_temperature"),
            "melting_temperature": th.get("melting_temperature"),
            "heat_deflection_temperature": None, "raw_source": "polyamide"})

    for i, p in enumerate(processing, 1):
        eid = f"PROC{i:05d}"
        ms = p.get("machine_settings", {})
        inj = ms.get("injection", {}).get("stages", []) or []
        hold_p = ms.get("holding", {}).get("pressures", []) or []
        hold_t = ms.get("holding", {}).get("times", []) or []
        cool = ms.get("cooling", {})
        rows["processing_cases"].append({
            "process_id": eid, "material_name": p.get("material_name"), "material_id": None,
            "sample_no": p["meta"].get("data_id"), "formulation": p.get("material_name"),
            "speed": inj[0] if inj else None, "pressure": hold_p[0] if hold_p else None,
            "pressure_time": hold_t[0] if hold_t else None,
            "cooling_temperature": cool.get("mold_temperature"),
            "cooling_time": cool.get("cooling_time"),
            "injection_rate": inj[0] if inj else None,
            "processing_temperature": cool.get("mold_temperature"), "raw_source": "processing"})
        w = p.get("WAXD_result", {})
        rows["waxd_results"].append({
            "waxd_id": f"{eid}_W", "process_id": eid, "sample_no": p["meta"].get("data_id"),
            "pa_content": None, "waxd_peak": None, "crystallinity": w.get("alpha_crystallinity"),
            "crystal_size": None, "orientation": None,
            "quality_value": w.get("alpha_100"), "raw_value": w.get("gamma")})
        me = p.get("mechanical", {})
        rows["performance_results"].append({
            "performance_id": f"{eid}_P", "process_id": eid, "sample_no": p["meta"].get("data_id"),
            "tensile_strength": me.get("tensile_strength"), "tensile_modulus": me.get("elastic_modulus"),
            "elongation": me.get("elongation_at_break"), "impact_strength": None,
            "composite_mechanical_property": me.get("yield_stress"), "raw_source": "processing"})

    for i, r in enumerate(pa6t, 1):
        cv = r.get("composition_variation", {})
        rows["pa6t_simulations"].append({
            "simulation_id": f"PA6T{i:06d}", "pa6t_content": cv.get("pa6t_content"),
            "temperature": r.get("temperature"), "density": r.get("density"),
            "energy": r.get("energy"),
            "transition_temperature": (r.get("temperature_range") or {}).get("lb"),
            "raw_source": "pa6t"})

    for t, cols in COLUMNS.items():
        with open(os.path.join(out_dir, t + ".csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(rows[t])
        print(f"{t:22} {len(rows[t]):>6} rows")
    print(f"total tables: {len(COLUMNS)}")


if __name__ == "__main__":
    main()
