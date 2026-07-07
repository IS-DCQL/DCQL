#!/usr/bin/env python3
"""Shared loader for the biomedical (TCGA) conversion scripts.

Merges the two raw GDC exports (clinical + biospecimen, already in English) into one
case-keyed record so the three storage structures all derive from the same logical data.

Raw sources (20-record teaching subset used for §6.2; the full TCGA cohort is used in
§6.4 performance and is obtained via the GDC link in the paper):
    biomedical-TCGA/clinical.cohort_20.json     -> case + project + demographic + diagnoses[]
    biomedical-TCGA/biospecimen.cohort_20.json  -> samples[] -> portions[] -> {slides[], analytes[] -> aliquots[]}
"""
import json, os

HERE = os.path.dirname(__file__)
RAW = os.path.join(HERE, "..", "..", "..", "biomedical-TCGA")
CLINICAL = os.path.join(RAW, "clinical.cohort_20.json")
BIOSPECIMEN = os.path.join(RAW, "biospecimen.cohort_20.json")


def load_cases():
    """Return a list of merged case documents, one per case_id."""
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
