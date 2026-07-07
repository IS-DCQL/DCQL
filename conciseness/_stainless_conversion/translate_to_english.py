#!/usr/bin/env python3
"""Translate the stainless-steel NMDMS raw data (DCM format) from Chinese to English.

Translates: all attribute keys (template + meta + content), the DCM _type values,
and a dictionary of common categorical content values. Numeric strings, element
symbols, grade codes, and free text are left as-is. Outputs *_en.json.
"""
import json, re, os

SRC = os.path.join(os.path.dirname(__file__), "..", "..", "..", "stainless-NMDMS")
OUT = os.path.dirname(__file__)

# ---- attribute-key map (exact) ----
KEYS = {
    # meta
    "数据 ID": "data_id", "标题": "title", "材料分类": "material_category",
    "数据摘要": "summary", "关键词": "keywords", "提交者": "submitter",
    "创建时间": "created_time", "来源": "source", "审核人": "reviewer",
    "其他信息": "other_info", "引用": "citation", "数据生产者": "data_producer",
    "数据生产机构": "data_producer_institution",
    # file 1: composition + mechanical
    "不锈钢牌号": "steel_grade", "成分": "composition",
    "试样状态及热处理方式": "specimen_state_and_heat_treatment",
    "试样形状": "specimen_shape", "热处理方式": "heat_treatment",
    "力学性能": "mechanical_properties", "断面收缩率": "reduction_of_area",
    "断后伸长率": "elongation_after_fracture", "屈服强度": "yield_strength",
    "抗拉强度": "tensile_strength", "布氏硬度": "brinell_hardness",
    "洛氏硬度": "rockwell_hardness", "维氏硬度": "vickers_hardness",
    # file 2: pitting corrosion
    "数据编号：": "data_number", "材料信息": "material_info", "牌号": "grade",
    "材料名称": "material_name", "加工工艺流程": "process_flow",
    "固溶温度（℃）": "solution_temperature_c", "组织结构": "microstructure",
    "产品形态": "product_form", "表面制备": "surface_preparation",
    "元素含量": "element_content", "材料性能": "material_performance",
    "屈服强度（MPa）": "yield_strength_mpa", "抗拉强度（wt%）": "tensile_strength_mpa",
    "硬度": "hardness", "实验参量——测试方法": "test_method", "方法名称": "method_name",
    "参考标准": "reference_standard", "仪器参数": "instrument_parameters",
    "除氧程序": "deoxygenation_procedure", "实验参量——试样表征": "specimen_characterization",
    "取样程序及位置": "sampling_procedure_and_location", "试样尺寸": "specimen_dimensions",
    "试样取向": "specimen_orientation", "表面粗糙度": "surface_roughness",
    "实验参量——溶液环境": "solution_environment", "溶液体积（mL）": "solution_volume_ml",
    "O2含量（ppm）": "O2_content_ppm", "溶液pH": "solution_ph", "流速": "flow_rate",
    "实验条件": "experimental_conditions", "实验温度（℃）": "temperature_c",
    "实验周期（h）": "duration_h", "扫描速度（mV/min）": "scan_rate_mv_min",
    "气体压力（MPa）": "gas_pressure_mpa", "结果表征": "result_characterization",
    "点蚀速率（mm/a）": "pitting_rate_mm_a", "点蚀电位Eb（V）": "pitting_potential_eb_v",
    "再钝化电位Ep（V）": "repassivation_potential_ep_v", "最大蚀坑深度（mm）": "max_pit_depth_mm",
    "蚀坑密度（N/cm^2）": "pit_density", "临界点蚀温度（CPT）": "critical_pitting_temperature_cpt",
    "腐蚀形貌图": "corrosion_morphology", "腐蚀产物表征": "corrosion_product_characterization",
    # DCM _type values
    "字符串型": "string", "数值型": "number", "范围型": "range",
    "表格型": "table", "图片型": "image",
}

def tkey(k):
    if k in KEYS:
        return KEYS[k]
    # generic: "溶液成分——NaCl（wt%）" -> "NaCl_wt"  (check before the bare wt% rule)
    m = re.match(r"^溶液成分——(.+?)（(wt%|mol/L)）$", k)
    if m:
        unit = "wt" if m.group(2) == "wt%" else "mol_l"
        return m.group(1) + "_" + unit
    # generic: element range  "Cr范围" -> "Cr_range"
    if k.endswith("范围"):
        return tkey(k[:-2]) + "_range"
    # generic: element weight-percent  "Cr（wt%）" -> "Cr_wt"
    m = re.match(r"^(.+?)（wt%）$", k)
    if m:
        return m.group(1) + "_wt"
    return k  # leave unknown keys (element symbols etc.) unchanged

# ---- categorical value map (exact match) ----
VALS = {
    "机器学习数据": "Machine Learning Data", "科技文献数据": "Scientific Literature Data",
    "奥氏体": "Austenite", "马氏体": "Martensite", "铁素体": "Ferrite",
    "双相": "Duplex", "奥氏体+铁素体": "Austenite+Ferrite", "奥氏体不锈钢": "Austenitic Stainless Steel",
    "棒材": "Bar", "板材": "Plate", "管材": "Tube", "带材": "Strip", "丝材": "Wire", "锻件": "Forging",
    "循环极化测试": "Cyclic Polarization Test", "动电位极化": "Potentiodynamic Polarization",
    "恒电位测试": "Potentiostatic Test", "浸泡试验": "Immersion Test", "无": "None", "admin": "admin",
}
# substring replacements for free-text terms (ORDER MATTERS: longest / most specific first,
# so a longer phrase is replaced before any of its sub-strings).
SUBS = [
    ("主要为不锈钢耐点蚀性能实验数据", "Mainly stainless-steel pitting-corrosion resistance experimental data"),
    ("主要包含不锈钢的成分", "Mainly the composition of stainless steel"),
    ("不锈钢耐点蚀性能实验", "Stainless-steel pitting-corrosion resistance experiment"),
    ("不锈钢力学性能", "Stainless-steel mechanical properties"),
    ("奥氏体不锈钢", "Austenitic stainless steel"),
    ("数据来源于科技文献", "Data sourced from scientific literature"),
    ("数据来源于标准", "Data sourced from standards"),
    ("动电位极化测试", "Potentiodynamic Polarization Test"),
    ("北京科技大学", "University of Science and Technology Beijing"),
    ("耐点蚀性能", "Pitting corrosion resistance"),
    ("力学性能等", "Mechanical properties, etc."),
    ("力学性能", "Mechanical properties"),
    ("再钝化电位", "repassivation_potential"), ("点蚀电位", "pitting_potential"),
    ("缓冷或", "Slow cooling or"), ("缓冷", "Slow cooling"), ("快冷", "Rapid cooling"),
    ("不锈钢", "Stainless steel"), ("张雷", "Zhang Lei"),
    ("固溶处理", "Solution Treatment"), ("固溶", "Solution"), ("时效处理", "Aging"),
    ("时效", "Aging"), ("退火", "Annealing"), ("淬火", "Quenching"), ("正火", "Normalizing"),
]

def tval(v):
    if not isinstance(v, str):
        return v
    if v in VALS:
        return VALS[v]
    out = v
    for zh, en in SUBS:
        out = out.replace(zh, en)
    return out

def walk(o):
    if isinstance(o, dict):
        return {tkey(k): walk(v) for k, v in o.items()}
    if isinstance(o, list):
        return [walk(x) for x in o]
    return tval(o)

def main():
    jobs = [("composition_and_mechanical.json", "stainless_mechanical_en.json"),
            ("pitting_corrosion_literature.json", "stainless_pitting_en.json")]
    for src, dst in jobs:
        data = json.load(open(os.path.join(SRC, src), encoding="utf-8"))
        out = walk(data)
        json.dump(out, open(os.path.join(OUT, dst), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        n = len(out) if isinstance(out, list) else 1
        recs = out[0].get("data", []) if isinstance(out, list) and out else []
        print(f"{src} -> {dst}: {len(recs)} records")

if __name__ == "__main__":
    main()
