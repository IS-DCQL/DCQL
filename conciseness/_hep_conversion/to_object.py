#!/usr/bin/env python3
"""Object structure for the HEP data: 3 classes (Table 2).
  1. Event    (1:N Particle)
  2. Particle (1:1 Momentum)
  3. Momentum (value type)"""
import json, os
HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, "..", "..", "..", "high-energy-physics-CERN", "output_events.json")
OUT = os.path.join(HERE, "object")

CLASSES = {
"Event.java": """@Entity
public class Event {
    @Id private Integer eventNumber;
    private String momentumUnit;
    private String lengthUnit;
    @OneToMany private List<Particle> particles;
}
""",
"Particle.java": """@Entity
public class Particle {
    @Id private Long particleId;
    private Integer pid;
    private Integer status;
    private Double mass;
    @Embedded private Momentum momentum;
    @ElementCollection private List<Integer> parentIds;
    @ElementCollection private List<Integer> childIds;
}
""",
"Momentum.java": """@Embeddable
public class Momentum {
    private Double px;
    private Double py;
    private Double pz;
    private Double e;
}
""",
}

def main():
    os.makedirs(OUT, exist_ok=True)
    for fn, src in CLASSES.items():
        open(os.path.join(OUT, fn), "w").write(src)
    events = json.load(open(SRC, encoding="utf-8"))
    graph = []
    for e in events:
        graph.append({"eventNumber": e["event_number"], "momentumUnit": e["momentum_unit"],
            "lengthUnit": e["length_unit"],
            "particles": [{"id": p["id"], "pid": p["pid"], "status": p["status"], "mass": p["mass"],
                "momentum": p["momentum"], "parentIds": p["parent_ids"], "childIds": p["child_ids"]}
                for p in e["particles"]]})
    json.dump(graph, open(os.path.join(OUT, "object_instances.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(f"{len(CLASSES)} object classes written:", ", ".join(c[:-5] for c in CLASSES))
    print(f"object graph: {len(graph)} Event instances")

if __name__ == "__main__":
    main()
