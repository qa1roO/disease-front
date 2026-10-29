"""Stage 3: build data/tree.json, the ICD-11 hierarchy of territories and provinces.

Rules (CONTEXT.md "Scope" and "Residual entries", docs/research/data-sources.md "Province count"):
- drop the non-disease chapters;
- drop residual entries ("other specified" / "unspecified"), trusting the IsResidual flag, not titles;
- a province is a remaining category with no children; every other kept entity is a territory,
  and a territory left with no children is dropped.
"""
import collections

from pipeline import icd11

# Symptoms, injury, external causes, factors influencing health, special purposes,
# traditional medicine, functioning, extension codes.
EXCLUDED_CHAPTERS = ("21", "22", "23", "24", "25", "26", "V", "X")


def build_tree(rows, version):
    kept = [r for r in rows if r["ChapterNo"] not in EXCLUDED_CHAPTERS and r["IsResidual"] != "True"]
    children = collections.defaultdict(list)
    for row in kept:
        children[row["Parent"]].append(row)  # tabulation order is ICD order

    counts = collections.Counter()

    def node(row):
        kind = row["ClassKind"]
        out = {
            "kind": kind,
            "code": row["ChapterNo"] if kind == "chapter" else row["Code"] or row["BlockId"],
            "title": row["Title"],
            "uri": row["Linearization URI"],
        }
        kids = [n for n in (node(c) for c in children[row["Foundation URI"]]) if n]
        if kids:
            out["children"] = kids
        elif kind != "category":
            return None
        counts["chapters" if kind == "chapter" else "territories" if kids else "provinces"] += 1
        return out

    chapters = [n for n in (node(r) for r in kept if r["ClassKind"] == "chapter") if n]
    return {
        "icd11": {
            "release": icd11.RELEASE,
            "version": version,
            "source": icd11.RELEASE_URL + "SimpleTabulation-ICD-11-MMS-en.zip",
            "citation": icd11.CITATION,
        },
        "excludedChapters": list(EXCLUDED_CHAPTERS),
        "counts": {k: counts[k] for k in ("chapters", "territories", "provinces")},
        "chapters": chapters,
    }
