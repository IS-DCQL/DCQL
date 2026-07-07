#!/usr/bin/env python3
"""Relational structure for the HEP data: 3 tables (Table 2).
  1. event         (event_number, momentum_unit, length_unit)
  2. particle      (event_number, particle_id, pid, status, mass, px, py, pz, e)
  3. particle_link (event_number, particle_id, child_id)   -- parent->child edges
"""
import json, os, csv
HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, "..", "..", "..", "high-energy-physics-CERN", "output_events.json")

def main():
    out = os.path.join(HERE, "relational"); os.makedirs(out, exist_ok=True)
    events = json.load(open(SRC, encoding="utf-8"))
    ev, par, link = [], [], []
    for e in events:
        en = e["event_number"]
        ev.append({"event_number": en, "momentum_unit": e["momentum_unit"],
                   "length_unit": e["length_unit"]})
        for p in e["particles"]:
            m = p["momentum"]
            par.append({"event_number": en, "particle_id": p["id"], "pid": p["pid"],
                        "status": p["status"], "mass": p["mass"],
                        "px": m["px"], "py": m["py"], "pz": m["pz"], "e": m["e"]})
            for c in p.get("child_ids", []):
                link.append({"event_number": en, "particle_id": p["id"], "child_id": c})
    for name, rows in [("event", ev), ("particle", par), ("particle_link", link)]:
        with open(os.path.join(out, name + ".csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader()
            w.writerows(rows)
    print("3 relational tables written:")
    print(f"  event: {len(ev)} | particle: {len(par)} | particle_link: {len(link)} rows")

if __name__ == "__main__":
    main()
