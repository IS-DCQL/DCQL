#!/usr/bin/env python3
"""Document structure for the high-energy-physics data: 1 collection (Table 2).
Each document = one event with its nested particles[]."""
import json, os
HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, "..", "..", "..", "high-energy-physics-CERN", "output_events.json")

def main():
    out = os.path.join(HERE, "document"); os.makedirs(out, exist_ok=True)
    events = json.load(open(SRC, encoding="utf-8"))
    json.dump(events, open(os.path.join(out, "events.json"), "w", encoding="utf-8"),
              ensure_ascii=False)
    print(f"collection events: {len(events)} documents")

if __name__ == "__main__":
    main()
