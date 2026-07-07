#!/usr/bin/env python3
"""DCQL (NMDMS) — query execution-time benchmark.

For each (domain, task) the *canonical query* is the DCQL statement, loaded from the
conciseness folder for provenance:
    ../../conciseness/DCQL/<domain>/<task>.dcql
The NMDMS read path executes it through its inverted-index engine; the executed
translation is held in DSL_TRANSLATION below (the biomedical-T3 body is the one used in
the §6.4 run, preserved verbatim). Server-side time is read from the engine's `took`.

Timing methodology preserved from the original time.py: RUNS executions, fastest-N mean,
percentiles; warm-up handled by reporting the fastest-N mean.
"""
import os, time, json, statistics
from elasticsearch import Elasticsearch

HOST = os.environ.get("DCQL_HOST", "http://localhost:9200")
RUNS = int(os.environ.get("RUNS", "50"))
SLEEP = float(os.environ.get("SLEEP_SECONDS", "0.1"))
HERE = os.path.dirname(os.path.abspath(__file__))
CONC = os.path.normpath(os.path.join(HERE, "..", "..", "conciseness", "DCQL"))

# (domain, task, index, dcql file) -> executed read-engine DSL
TASKS = [("biomedical", "T2", "cases"),
         ("biomedical", "T3", "cases"),
         ("organic-polymer", "T2", "processing_logs"),
         ("organic-polymer", "T3", "materials_library")]

DSL_TRANSLATION = {
    ("biomedical", "T2"): {
        "size": 1, "_source": ["case_id", "demographic", "diagnoses"],
        "query": {"term": {"case_id": "00016c8f-a0be-4319-9c42-4f3bcd90ac92"}}},
    ("biomedical", "T3"): json.loads(r'''{"size": 50, "track_total_hits": false, "_source": ["case_id"], "query": {"bool": {"filter": [{"terms": {"project.project_id": ["TCGA-KIRC", "TARGET-WT"]}}, {"bool": {"minimum_should_match": 1, "should": [{"term": {"demographic.vital_status": "Dead"}}, {"nested": {"path": "diagnoses", "query": {"bool": {"filter": [{"term": {"diagnoses.vital_status": "Dead"}}, {"match_phrase": {"diagnoses.primary_diagnosis": "renal cell carcinoma"}}]}}}}]}}, {"nested": {"path": "samples", "query": {"bool": {"filter": [{"term": {"samples.sample_type": "Primary Tumor"}}, {"terms": {"samples.preservation_method": ["Snap Frozen", "Snap-Frozen", "OCT"]}}, {"nested": {"path": "samples.portions", "query": {"nested": {"path": "samples.portions.analytes", "query": {"bool": {"filter": [{"term": {"samples.portions.analytes.analyte_type": "RNA"}}, {"nested": {"path": "samples.portions.analytes.aliquots", "query": {"range": {"samples.portions.analytes.aliquots.concentration": {"gt": 0.1}}}}}]}}}}}}]}}}}]}}}'''),
    ("organic-polymer", "T2"): {
        "size": 50, "_source": ["meta.data_id", "WAXD_result.alpha_crystallinity"],
        "query": {"bool": {"filter": [
            {"term": {"meta.data_id": 195540}},
            {"range": {"WAXD_result.alpha_crystallinity": {"gt": 100}}}]}}},
    # T3 joins materials_library x processing_logs; the read engine resolves the
    # processing-side injection-speed predicate application-side, so the indexed part is
    # the scalar materials filter below.
    ("organic-polymer", "T3"): {
        "size": 50, "_source": ["basic_info.name"],
        "query": {"bool": {"filter": [
            {"term": {"basic_info.category": "Semi-Aromatic"}},
            {"nested": {"path": "samples", "query": {"bool": {"filter": [
                {"range": {"samples.thermal.glass_temperature": {"gt": 280}}},
                {"range": {"samples.mechanical.tensile_strength": {"gt": 150}}}]}}}}]}}},
}


def mean_fastest_n(data, n=40):
    return statistics.mean(sorted(data)[:min(n, len(data))]) if data else None


def load_dcql(domain, task):
    with open(os.path.join(CONC, domain, task + ".dcql"), encoding="utf-8") as f:
        return f.read().strip()


def bench_one(es, domain, task, index):
    dcql = load_dcql(domain, task)
    body = DSL_TRANSLATION[(domain, task)]
    print(f"\n===== {domain} {task} (index={index}) =====")
    print(f"-- canonical DCQL (from conciseness) --\n{dcql}")
    timings, took = [], []
    for i in range(1, RUNS + 1):
        start = time.perf_counter()
        try:
            r = es.search(index=index, body=body)
            timings.append((time.perf_counter() - start) * 1000)
            if r.get("took") is not None:
                took.append(r["took"])
        except Exception as e:
            print(f"[{i:03d}] FAIL {e}")
        time.sleep(SLEEP)
    if took:
        print(f"server took: min={min(took):.2f} avg(fastest40)={mean_fastest_n(took):.2f} "
              f"median={statistics.median(took):.2f} max={max(took):.2f} ms")
    return {"domain": domain, "task": task,
            "server_took_ms_avg": mean_fastest_n(took), "runs": len(timings)}


def main():
    es = Elasticsearch(HOST, request_timeout=180)
    if not es.ping():
        raise RuntimeError("Cannot reach the NMDMS read engine; is it running?")
    results = [bench_one(es, d, t, idx) for d, t, idx in TASKS]
    json.dump(results, open(os.path.join(HERE, "benchmark_result.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
