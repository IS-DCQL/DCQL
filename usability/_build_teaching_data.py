#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the illustrative ~20-record teaching datasets handed out with the exam papers.

Output goes to exam-blank/dataset/<domain>/document/. These are ILLUSTRATIVE teaching sets
(document/nested form) curated so the three result-prediction questions return small,
predictable, NON-empty results -- mirroring the §6.3 design goal ("about 20 core records,
ensuring the query results are predictable"). They are derived from the real sources but
deliberately curated:
  * biomedical: 20 cases, including one real qualifying TCGA case so biomedical-Q4 returns a
    small result; the rest are the §6.2 teaching subset.
  * stainless : 20 pitting records; yield_strength_mpa is INJECTED into material_performance
    (the real corrosion files leave it empty) so stainless-Q4 (which requires yield>550) is
    answerable -- 2 records are made to satisfy all conditions.
  * high-energy-physics: the 20 real events (the electron filter already returns results).
  * organic-polymer: 20 representative materials/processing/pa6t records (no prediction item).

The relational (SQL) and object (OQL) renderings of the same logical records are produced by
running conciseness/_<domain>_conversion/ on these files; see exam-blank/dataset/README.md.

NOTE: RAW and HEP_RAW below are the on-disk source-data directories, whose names are in the
original (Chinese) form -- these string literals must match the actual folder names, so they
are kept verbatim; everything this script emits is English.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))                 # code_submission/usability
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))           # repository root
CONC = os.path.normpath(os.path.join(HERE, "..", "conciseness"))
OUT = os.path.join(HERE, "exam-blank", "dataset")
RAW = os.path.join(ROOT, "biomedical-TCGA")           # source dir (name kept to match disk)
HEP_RAW = os.path.join(ROOT, "high-energy-physics-CERN")        # source dir (name kept to match disk)


def dump(domain, coll, docs):
    d = os.path.join(OUT, domain, "document")
    os.makedirs(d, exist_ok=True)
    json.dump(docs, open(os.path.join(d, coll + ".json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return len(docs)


def fnum(x):
    try: return float(x)
    except: return None


# ---------------- biomedical -------------------------------------------------------
def build_biomedical():
    clin = json.load(open(os.path.join(RAW, "clinical.cohort.json"), encoding="utf-8"))
    bio = json.load(open(os.path.join(RAW, "biospecimen.cohort.json"), encoding="utf-8"))
    clin_by = {c["case_id"]: c for c in clin}
    bio_by = {b["case_id"]: b for b in bio}
    QUALIFIER = "28011111-4a01-4cdc-8d6b-7223fb2c501b"      # real TCGA case satisfying Q4
    teach20 = json.load(open(os.path.join(RAW, "clinical.cohort_20.json"), encoding="utf-8"))
    ids = [QUALIFIER] + [c["case_id"] for c in teach20 if c["case_id"] != QUALIFIER][:19]
    cases = []
    for cid in ids:
        c = clin_by.get(cid, {"case_id": cid})
        b = bio_by.get(cid, {})
        cases.append({
            "case_id": cid, "project": c.get("project", {}),
            "primary_site": c.get("primary_site"), "disease_type": c.get("disease_type"),
            "submitter_id": c.get("submitter_id"), "state": c.get("state"),
            "demographic": c.get("demographic", {}) or {},
            "diagnoses": c.get("diagnoses", []) or [],
            "samples": b.get("samples", []) or [],
        })
    dump("biomedical", "cases", cases)
    def low(x): return (x or "").lower()
    hits = []
    for c in cases:
        if (c.get("project") or {}).get("project_id") not in ("TCGA-KIRC", "TARGET-WT"): continue
        dm = c.get("demographic") or {}
        if not (low(dm.get("vital_status")) == "dead" or any(
                low(d.get("vital_status")) == "dead" and "renal cell carcinoma" in low(d.get("primary_diagnosis"))
                for d in c.get("diagnoses", []))):
            continue
        for s in c.get("samples", []):
            if s.get("sample_type") != "Primary Tumor": continue
            if s.get("preservation_method") not in ("Snap Frozen", "Snap-Frozen", "OCT"): continue
            for p in s.get("portions", []) or []:
                for an in p.get("analytes", []) or []:
                    if an.get("analyte_type") != "RNA": continue
                    for al in an.get("aliquots", []) or []:
                        if (fnum(al.get("concentration")) or 0) > 0.1:
                            hits.append((c["case_id"], al.get("aliquot_id"), al.get("concentration")))
    return ("biomedical-Q4", len(cases), hits)


# ---------------- stainless --------------------------------------------------------
def build_stainless():
    src = os.path.join(CONC, "_stainless_conversion", "stainless_pitting_en.json")
    if not os.path.exists(src):
        os.system(f'cd "{os.path.join(CONC, "_stainless_conversion")}" && python3 translate_to_english.py >/dev/null 2>&1')
    pit = json.load(open(src, encoding="utf-8"))["data"]
    def cond(c):
        se = (c.get("solution_environment") or [{}])[0]
        ec = (c.get("experimental_conditions") or [{}])[0]
        rc = (c.get("result_characterization") or [{}])[0]
        return (fnum(se.get("NaCl_wt")) == 3.5 and fnum(ec.get("temperature_c")) == 20
                and (fnum(rc.get("pitting_potential_eb_v")) or -9) > 1.0)
    matching = [r for r in pit if cond(r["content"])]
    others = [r for r in pit if not cond(r["content"])]
    chosen = matching[:6] + others[:14]            # 20 total, 6 satisfy env/Eb conditions
    # INJECT yield_strength_mpa (the real corrosion files leave material_performance empty):
    # make exactly 2 of the matching records satisfy yield>550, others below/absent.
    inject = {0: 615.0, 1: 580.0, 2: 520.0, 3: 498.0}   # index within `matching`
    q4 = []
    for r in chosen:
        c = r["content"]
        if r in matching:
            mi = matching.index(r)
            y = inject.get(mi)
            c["material_performance"] = [{"yield_strength_mpa": y}] if y is not None else []
            if y is not None and y > 550 and cond(c):
                q4.append((c.get("data_number"), (c.get("material_info") or [{}])[0].get("material_name"), y))
        else:
            c.setdefault("material_performance", [])
    dump("stainless-steel", "pitting_corrosion", chosen)
    msrc = os.path.join(CONC, "_stainless_conversion", "stainless_mechanical_en.json")
    if os.path.exists(msrc):
        mech = json.load(open(msrc, encoding="utf-8"))["data"][:20]
        dump("stainless-steel", "mechanical_properties", mech)
    return ("stainless-Q4", len(chosen), q4)


# ---------------- high-energy-physics ----------------------------------------------
def build_hep():
    ev = json.load(open(os.path.join(HEP_RAW, "output_events.json"), encoding="utf-8"))
    if isinstance(ev, dict):
        ev = ev.get("data", ev.get("events", [ev]))
    ev = ev[:20]
    dump("high-energy-physics", "events", ev)
    per, tot = [], 0
    for e in ev:
        hits = [p for p in e.get("particles", []) if p.get("pid") in (11, -11) and p.get("status") == 1]
        per.append((e.get("event_number"), len(hits))); tot += len(hits)
    return ("hep-Q3", len(ev), {"events": len(ev), "total_e": tot, "per_event": per})


# ---------------- organic-polymer (no prediction item) -----------------------------
def build_polymer():
    base = os.path.join(CONC, "_polymer_conversion")
    for f in ("materials_library_en.json", "processing_logs_en.json", "pa6t_library_en.json"):
        if not os.path.exists(os.path.join(base, f)):
            os.system(f'cd "{base}" && python3 translate_to_english.py >/dev/null 2>&1')
            break
    mats = json.load(open(os.path.join(base, "materials_library_en.json"), encoding="utf-8"))
    semi = [m for m in mats if m["basic_info"].get("category") == "Semi-Aromatic"][:10]
    rest = [m for m in mats if m not in semi][:10]
    dump("organic-polymer", "materials_library", semi + rest)
    proc = json.load(open(os.path.join(base, "processing_logs_en.json"), encoding="utf-8"))[:20]
    dump("organic-polymer", "processing_logs", proc)
    pa = json.load(open(os.path.join(base, "pa6t_library_en.json"), encoding="utf-8"))[:20]
    dump("organic-polymer", "pa6t_library", pa)
    return ("polymer", len(semi + rest), None)


def main():
    for fn in (build_biomedical, build_stainless, build_hep, build_polymer):
        tag, n, res = fn()
        print(f"[{tag}] {n} records | prediction result: {res}")


if __name__ == "__main__":
    main()
