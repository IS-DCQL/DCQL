#!/usr/bin/env python3
"""Relational structure for the stainless-steel data: 8 tables (Table 2).

Normalizes the two source files into 8 tables (3NF), emitting one CSV per table
plus schema.sql (DDL).

  From mechanical_properties:
    1. steel               (steel_id, grade, specimen_shape, heat_treatment)
    2. composition         (steel_id, element, content, content_range, unit)
    3. mechanical_property (steel_id, reduction_of_area, elongation_after_fracture,
                            yield_strength, tensile_strength, brinell_hardness,
                            rockwell_hardness, vickers_hardness)
  From pitting_corrosion:
    4. pitting_experiment  (exp_id, grade, material_name, solution_temperature_c,
                            microstructure, product_form, surface_preparation,
                            method_name, reference_standard,
                            yield_strength_mpa, tensile_strength_mpa, hardness)
    5. element_content     (exp_id, element, content_wt)
    6. solution_environment(exp_id, NaCl_wt, FeCl3_wt, H2SO4_mol_l, HCl_mol_l,
                            H3PO4_mol_l, CuCl2_wt, solution_volume_ml,
                            O2_content_ppm, solution_ph, flow_rate)
    7. experimental_condition (exp_id, temperature_c, duration_h,
                            scan_rate_mv_min, gas_pressure_mpa)
    8. corrosion_result    (exp_id, pitting_rate_mm_a, pitting_potential_eb_v,
                            repassivation_potential_ep_v, max_pit_depth_mm,
                            pit_density, critical_pitting_temperature_cpt)
"""
import json, os, csv
HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "relational")

def first(rec_content, group):
    g = rec_content.get(group, [])
    return g[0] if isinstance(g, list) and g else {}

ELEMENTS = ["C","Si","Mn","P","S","Cr","Ni","Mo","Cu","N","Nb","Ti","Al","W","Ce","Fe"]
COMP_ELEMENTS = ["C","Ni","Mn","Mo","Cr","N","S","P","Si","Cu"]

def build():
    os.makedirs(OUT, exist_ok=True)
    tables = {n: [] for n in ["steel","composition","mechanical_property","pitting_experiment",
              "element_content","solution_environment","experimental_condition","corrosion_result"]}

    # ---- mechanical_properties file ----
    mech = json.load(open(os.path.join(HERE,"stainless_mechanical_en.json"),encoding="utf-8"))["data"]
    for r in mech:
        sid = r["meta"]["data_id"]; c = r["content"]
        st = first(c,"specimen_state_and_heat_treatment")
        tables["steel"].append({"steel_id":sid,
            "grade": (c.get("steel_grade") or "").strip(),
            "specimen_shape": st.get("specimen_shape",""),
            "heat_treatment": st.get("heat_treatment","")})
        comp = first(c,"composition")
        for el in COMP_ELEMENTS:
            if el in comp or (el+"_range") in comp:
                tables["composition"].append({"steel_id":sid,"element":el,
                    "content":comp.get(el,""),"content_range":comp.get(el+"_range",""),"unit":"%"})
        mp = first(c,"mechanical_properties")
        if mp:
            tables["mechanical_property"].append({"steel_id":sid,
                "reduction_of_area":mp.get("reduction_of_area",""),
                "elongation_after_fracture":mp.get("elongation_after_fracture",""),
                "yield_strength":mp.get("yield_strength",""),
                "tensile_strength":mp.get("tensile_strength",""),
                "brinell_hardness":mp.get("brinell_hardness",""),
                "rockwell_hardness":mp.get("rockwell_hardness",""),
                "vickers_hardness":mp.get("vickers_hardness","")})

    # ---- pitting_corrosion file ----
    pit = json.load(open(os.path.join(HERE,"stainless_pitting_en.json"),encoding="utf-8"))["data"]
    for r in pit:
        eid = r["meta"]["data_id"]; c = r["content"]
        mi = first(c,"material_info"); perf = first(c,"material_performance"); tm = first(c,"test_method")
        tables["pitting_experiment"].append({"exp_id":eid,
            "grade":mi.get("grade",""),"material_name":mi.get("material_name",""),
            "solution_temperature_c":mi.get("solution_temperature_c",""),
            "microstructure":mi.get("microstructure",""),"product_form":mi.get("product_form",""),
            "surface_preparation":mi.get("surface_preparation",""),
            "method_name":tm.get("method_name",""),"reference_standard":tm.get("reference_standard",""),
            "yield_strength_mpa":perf.get("yield_strength_mpa",""),
            "tensile_strength_mpa":perf.get("tensile_strength_mpa",""),"hardness":perf.get("hardness","")})
        ec = first(c,"element_content")
        for el in ELEMENTS:
            if (el+"_wt") in ec:
                tables["element_content"].append({"exp_id":eid,"element":el,"content_wt":ec.get(el+"_wt","")})
        se = first(c,"solution_environment")
        tables["solution_environment"].append({"exp_id":eid,
            **{k:se.get(k,"") for k in ["NaCl_wt","FeCl3_wt","H2SO4_mol_l","HCl_mol_l","H3PO4_mol_l",
               "CuCl2_wt","solution_volume_ml","O2_content_ppm","solution_ph","flow_rate"]}})
        cond = first(c,"experimental_conditions")
        tables["experimental_condition"].append({"exp_id":eid,
            **{k:cond.get(k,"") for k in ["temperature_c","duration_h","scan_rate_mv_min","gas_pressure_mpa"]}})
        res = first(c,"result_characterization")
        tables["corrosion_result"].append({"exp_id":eid,
            **{k:res.get(k,"") for k in ["pitting_rate_mm_a","pitting_potential_eb_v",
               "repassivation_potential_ep_v","max_pit_depth_mm","pit_density","critical_pitting_temperature_cpt"]}})
    return tables

def main():
    tables = build()
    for name, rows in tables.items():
        if not rows: rows=[{}]
        with open(os.path.join(OUT,name+".csv"),"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader()
            for r in rows: w.writerow(r)
    print(f"{len(tables)} relational tables written:")
    for n,rows in tables.items(): print(f"  {n}: {len(rows)} rows")

if __name__ == "__main__":
    main()
