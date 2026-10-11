"""Round 3, step 1: apply the pre-registered condition C2 (SPEC.md) to all 16 profiles, before scoring_v2.php exists.

Output: predictions_round3.json (commit and push before writing or running the redesigned engine).
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBES = HERE.parent


def load():
    rows = []
    for f in (PROBES / "profiles.json", PROBES / "profiles_external.json", HERE / "profiles_round3.json"):
        spec = json.loads(f.read_text(encoding="utf-8"))
        edpex = json.loads((PROBES / "profiles.json").read_text(encoding="utf-8"))["edpex_scale"]  # external file says "inherited"
        for p in spec["profiles"]:
            rows.append((p, edpex))
    return rows


def c2(p, edpex):
    cats = p["categories"]
    a = all(c[1] in ("process", "results") for c in cats)
    sides = sorted({c[1] for c in cats if c[1] in ("process", "results")} | ({"results", "process"} if not a else set()))
    b, c = True, True
    for s in sides:
        scale = edpex if p[s]["scale"] == "edpex" else p[s]["scale"]
        b &= bool(scale) and all(isinstance(v, int) for band in scale for v in band) and all(band for band in scale)
        c &= len(p[s]["factors"]) >= 1 and p[s]["levels"] >= 2 and len(scale) <= p[s]["levels"]
    return {"C2a_one_rubric_per_category": a, "C2b_finite_integer_bands": b, "C2c_bands_not_above_levels": c}


def main():
    out = []
    for p, edpex in load():
        cl = c2(p, edpex)
        out.append({"id": p["id"], "kind": p["kind"], "clauses": cl,
                    "predicted": "configuration only" if all(cl.values()) else "dedicated module"})
    (HERE / "predictions_round3.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    for r in out:
        print(f"{r['id']:10s} {r['predicted']:20s} {[k for k, v in r['clauses'].items() if not v]}")


if __name__ == "__main__":
    main()
