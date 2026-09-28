"""Round 2, step 1: predictions for frameworks defined by outside bodies.

The revised condition of refine.py (R1 category 7 is the only results category; R2 the six EdPEx
bands; R3 four factors on six levels) was derived from round 1 and has not been tested on new
cases. This script applies it, unchanged, to the external profiles and writes the predictions
before probes/observe_external.php is run.

Output: predictions_external.json
"""
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EDPEX_BANDS = 6


def predict(p):
    cats = p["categories"]
    r1 = all((c[1] == "results") == (c[0] == 7) and c[1] in ("process", "results") for c in cats) and any(c[0] == 7 for c in cats)
    r2 = all(p[s]["scale"] == "edpex" for s in ("process", "results"))
    r3 = all(len(p[s]["factors"]) == 4 and p[s]["levels"] == EDPEX_BANDS for s in ("process", "results"))
    return {"R1_results_is_category_7": r1, "R2_edpex_bands": r2, "R3_four_factors_six_levels": r3}


def main():
    spec = json.loads((HERE / "profiles_external.json").read_text(encoding="utf-8"))
    rows = []
    for p in spec["profiles"]:
        c = predict(p)
        rows.append({"id": p["id"], "kind": p["kind"], "clauses": c,
                     "predicted": "configuration only" if all(c.values()) else "dedicated module"})
    out = {"written_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "condition": "revised condition from refine.py (R1, R2, R3), applied unchanged",
           "predictions": rows}
    (HERE / "predictions_external.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    for r in rows:
        print(f'{r["id"]:<10} predicted {r["predicted"]}')


if __name__ == "__main__":
    main()
