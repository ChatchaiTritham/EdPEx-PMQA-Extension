"""Step 1 of the prospective test: predictions from the published structural condition, recorded before observation.

The condition is applied exactly as stated in the extension protocol of the article (Algorithm 1, tag v1.2.0):
a framework enters as configuration if it has seven categories, one results category, points totalling 1,000,
and ADLI/LeTCI evaluation. "ADLI/LeTCI evaluation" is read as: process categories rated on the four ADLI
factors and results categories on the four LeTCI factors. The condition says nothing about how categories are
numbered or which scoring bands are used, so it cannot reject a profile on those grounds.

Output: predictions.json. This file is committed before observe.php is run.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ADLI = ["Approach", "Deployment", "Learning", "Integration"]
LETCI = ["Levels", "Trends", "Comparisons", "Integration"]


def clauses(p):
    cats = p["categories"]
    points = [c[2] for c in cats]
    return {
        "seven_categories": len(cats) == 7,
        "one_results_category": sum(1 for c in cats if c[1] == "results") == 1 and all(c[1] in ("process", "results") for c in cats),
        "points_total_1000": all(x is not None for x in points) and sum(points) == 1000,
        "adli_letci_evaluation": p["process"]["factors"] == ADLI and p["results"]["factors"] == LETCI,
    }


def main():
    profiles = json.loads((HERE / "profiles.json").read_text(encoding="utf-8"))["profiles"]
    out = []
    for p in profiles:
        c = clauses(p)
        out.append({"id": p["id"], "kind": p["kind"], "clauses": c,
                    "predicted": "configuration only" if all(c.values()) else "dedicated module"})
    (HERE / "predictions.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    for r in out:
        failed = [k for k, v in r["clauses"].items() if not v]
        print(f"{r['id']:10s} {r['predicted']:20s} violated: {', '.join(failed) or '-'}")


if __name__ == "__main__":
    main()
