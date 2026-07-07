#!/usr/bin/env python3
"""Object structure for the stainless-steel data: 5 classes (Table 2).

Emits the 5 persistent-class definitions (Java/JPA entities) and builds the object
graph from the data (serialized to object_instances.json as evidence the data fits
the 5-class model).

  1. Steel              (1:N Composition, 1:1 MechanicalProperty)
  2. Composition        (value type of Steel)
  3. MechanicalProperty (value type of Steel)
  4. PittingExperiment  (embeds element content / solution env / conditions;
                         1:1 CorrosionResult)
  5. CorrosionResult    (value type of PittingExperiment)
"""
import json, os
HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "object")

CLASSES = {
"Steel.java": """@Entity
public class Steel {
    @Id private String steelId;
    private String grade;
    private String specimenShape;
    private String heatTreatment;
    @ElementCollection private List<Composition> composition;
    @Embedded private MechanicalProperty mechanicalProperty;
}
""",
"Composition.java": """@Embeddable
public class Composition {
    private String element;
    private Double content;
    private String contentRange;
    private String unit;
}
""",
"MechanicalProperty.java": """@Embeddable
public class MechanicalProperty {
    private Double reductionOfArea;
    private Double elongationAfterFracture;
    private Double yieldStrength;
    private Double tensileStrength;
    private String brinellHardness;
    private String rockwellHardness;
    private String vickersHardness;
}
""",
"PittingExperiment.java": """@Entity
public class PittingExperiment {
    @Id private String expId;
    private String grade;
    private String materialName;
    private String microstructure;
    private String methodName;
    private Double yieldStrengthMpa;
    @ElementCollection private Map<String, String> elementContent;
    private Double naclWt;
    private Double temperatureC;
    private Double scanRateMvMin;
    @Embedded private CorrosionResult result;
}
""",
"CorrosionResult.java": """@Embeddable
public class CorrosionResult {
    private Double pittingRateMmA;
    private Double pittingPotentialEbV;
    private Double repassivationPotentialEpV;
    private Double maxPitDepthMm;
    private String pitDensity;
    private String criticalPittingTemperatureCpt;
}
""",
}

def num(x):
    try: return float(x)
    except (TypeError, ValueError): return None

def first(c, g):
    v = c.get(g, []); return v[0] if isinstance(v, list) and v else {}

def main():
    os.makedirs(OUT, exist_ok=True)
    for fn, src in CLASSES.items():
        open(os.path.join(OUT, fn), "w").write(src)

    graph = {"Steel": [], "PittingExperiment": []}
    mech = json.load(open(os.path.join(HERE,"stainless_mechanical_en.json"),encoding="utf-8"))["data"]
    for r in mech:
        c=r["content"]; comp=first(c,"composition"); st=first(c,"specimen_state_and_heat_treatment"); mp=first(c,"mechanical_properties")
        graph["Steel"].append({"steelId":r["meta"]["data_id"],"grade":(c.get("steel_grade") or "").strip(),
            "specimenShape":st.get("specimen_shape"),"heatTreatment":st.get("heat_treatment"),
            "composition":[{"element":e,"content":num(comp.get(e)),"contentRange":comp.get(e+"_range"),"unit":"%"}
                           for e in ["C","Ni","Mn","Mo","Cr","N","S","P","Si","Cu"] if e in comp or e+"_range" in comp],
            "mechanicalProperty":{"yieldStrength":num(mp.get("yield_strength")),"tensileStrength":num(mp.get("tensile_strength")),
                "reductionOfArea":num(mp.get("reduction_of_area")),"elongationAfterFracture":num(mp.get("elongation_after_fracture"))} if mp else None})
    pit = json.load(open(os.path.join(HERE,"stainless_pitting_en.json"),encoding="utf-8"))["data"]
    for r in pit:
        c=r["content"]; mi=first(c,"material_info"); perf=first(c,"material_performance")
        se=first(c,"solution_environment"); cond=first(c,"experimental_conditions"); res=first(c,"result_characterization")
        ec=first(c,"element_content")
        graph["PittingExperiment"].append({"expId":r["meta"]["data_id"],"grade":mi.get("grade"),
            "materialName":mi.get("material_name"),"microstructure":mi.get("microstructure"),
            "methodName":first(c,"test_method").get("method_name"),"yieldStrengthMpa":num(perf.get("yield_strength_mpa")),
            "elementContent":{k[:-3]:v for k,v in ec.items() if k.endswith("_wt")},
            "naclWt":num(se.get("NaCl_wt")),"temperatureC":num(cond.get("temperature_c")),"scanRateMvMin":num(cond.get("scan_rate_mv_min")),
            "result":{"pittingPotentialEbV":num(res.get("pitting_potential_eb_v")),
                "repassivationPotentialEpV":num(res.get("repassivation_potential_ep_v")),
                "pittingRateMmA":num(res.get("pitting_rate_mm_a")),"maxPitDepthMm":num(res.get("max_pit_depth_mm")),
                "pitDensity":res.get("pit_density"),"criticalPittingTemperatureCpt":res.get("critical_pitting_temperature_cpt")}})
    json.dump(graph, open(os.path.join(OUT,"object_instances.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"{len(CLASSES)} object classes written:", ", ".join(c[:-5] for c in CLASSES))
    print(f"object graph: {len(graph['Steel'])} Steel + {len(graph['PittingExperiment'])} PittingExperiment instances")

if __name__ == "__main__":
    main()
