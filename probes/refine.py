"""Step 3 (post hoc): the condition revised in the light of the observations, checked against the same profiles.

Revised condition, stated in terms of what the engine assumes:
  R1 category 7 is the only results category, every other category is a process category, and no category is
     evaluated with both rubrics;
  R2 both schemes use the six EdPEx scoring bands with their permitted percentages;
  R3 each scheme rates four factors on six levels.
The point total is dropped because no engine function uses it.

Because the revision was made after seeing the observations, agreement here is a consistency check, not a
test; the revised condition needs new cases to be tested.
Output: refined.json
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def revised(p, edpex_scale):
    cats = p["categories"]
    r1 = all((c[1] == "results") == (c[0] == 7) and c[1] in ("process", "results") for c in cats) and any(c[0] == 7 for c in cats)
    r2 = all((edpex_scale if p[s]["scale"] == "edpex" else p[s]["scale"]) == edpex_scale for s in ("process", "results"))
    r3 = all(len(p[s]["factors"]) == 4 and p[s]["levels"] == 6 for s in ("process", "results"))
    return {"R1_results_is_category_7": r1, "R2_edpex_bands": r2, "R3_four_factors_six_levels": r3}


def main():
    spec = json.loads((HERE / "profiles.json").read_text(encoding="utf-8"))
    observed = {r["id"]: r["observed"] for r in json.loads((HERE / "observations.json").read_text(encoding="utf-8"))["profiles"]}
    rows = []
    for p in spec["profiles"]:
        c = revised(p, spec["edpex_scale"])
        verdict = "configuration only" if all(c.values()) else "dedicated module"
        rows.append({"id": p["id"], "clauses": c, "revised_condition": verdict, "observed": observed[p["id"]],
                     "agrees": verdict == observed[p["id"]]})
    out = {"post_hoc": True, "profiles": rows, "agreements": sum(r["agrees"] for r in rows), "total": len(rows)}
    (HERE / "refined.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"revised condition agrees with observation on {out['agreements']}/{out['total']} profiles (post hoc)")


if __name__ == "__main__":
    main()
