"""Stage 4: cross-walk every province to a GBD cause and size it by that cause's burden.

Rules (docs/spec/v1.md "Cross-walk rules (stage 4)"):
- ICD-11 province -> its one ICD-10 code (WHO 11To10MapToOneCategory) -> the GBD cause whose code list holds it.
- A code that is an ICD-10 category, block range or chapter is expanded to the ICD-10 leaf codes under it, and each
  leaf votes for its cause: majority rule. Ties go to data/crosswalk-review.yaml with the first candidate (in GBD
  order) as a placeholder resolution, which the owner edits by hand; a null resolution leaves the province in fog.
- A leaf belongs to the first GBD causes whose code list holds it, looking in this order (see lookup_steps):
  cause-of-death lists, the project's codes for causes GBD lists none for (data/gbd-extra-codes.yaml), nonfatal
  lists, then parent groups standing in for causes with no codes at all (pipeline/gbd.py, groups).
- A GBD cause's DALYs are split equally among its provinces; a cause with more than one province marks them
  "estimated". A province with no GBD cause gets no burden: minimum size, fog.

The resulting ICD-11 -> GBD cause table is the project's own work (docs/research/data-sources.md, "Licence decisions").
"""
import collections
import re

NOTE = ("Project-made cross-walk from ICD-11 to GBD causes, built from WHO's ICD-11 -> ICD-10 mapping table "
        "(11To10MapToOneCategory) and IHME's GBD cause -> ICD-10 code lists. It is not a WHO or IHME product.")
ROMAN = re.compile(r"^[IVXL]+$")


def code_key(code):
    """An ICD-10 code in a form that compares across notations: 'E10.9' and 'E109' are both 'E109'."""
    return code.strip().upper().replace(".", "")


def parse_code_list(text):
    """'A00-A00.9, B63' -> [('A00', 'A009'), ('B63', 'B63')]."""
    ranges = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        lo, _, hi = part.partition("-")
        ranges.append((code_key(lo), code_key(hi or lo)))
    return ranges


def in_range(key, lo, hi):
    """A code is inside lo-hi if it sorts between them or sits under hi (hi 'A70' holds 'A70.0')."""
    return lo <= key and (key <= hi or key.startswith(hi))


def in_ranges(key, ranges):
    return any(in_range(key, lo, hi) for lo, hi in ranges)


class Icd10:
    """The ICD-10 codes WHO's mapping tables know, to expand a category, block or chapter into its leaf codes."""

    def __init__(self, codes):
        self.chapter = {code_key(c): ch for c, ch in codes}
        parents = {k[:n] for k in self.chapter for n in range(3, len(k))}
        self.leaves = sorted(k for k in self.chapter if k not in parents)

    def expand(self, target):
        target = target.strip()
        if not target or target == "No Mapping":
            return []
        if ROMAN.match(target):
            return [k for k in self.leaves if self.chapter[k] == target]
        if "-" in target:
            ((lo, hi),) = parse_code_list(target)
            return [k for k in self.leaves if in_range(k, lo, hi)]
        key = code_key(target)
        return [k for k in self.leaves if k.startswith(key)] or [key]


def lookup_steps(in_scope, groups):
    """The order a leaf code's cause is looked up in: the most-detailed causes' cause-of-death lists, then the
    project's own codes for them, then GBD's nonfatal lists, then the parent groups, deepest level first.

    The nonfatal lists are case definitions for hospital data and can be broad (bipolar disorder's runs F30-F34.0,
    taking in every depressive episode), so a named project code beats them."""
    steps = [("cod", in_scope), ("project", in_scope), ("nonfatal", in_scope)]
    for level in sorted({g["level"] for g in groups.values()}, reverse=True):
        members = {c for c, g in groups.items() if g["level"] == level}
        steps += [("cod", members), ("nonfatal", members)]
    return steps


class CauseIndex:
    """GBD cause -> ICD-10 code lists, searched step by step (see lookup_steps); the first step with a match wins."""

    def __init__(self, rows, steps):
        # step -> first letter -> [(lo, hi, cause_id)], so a lookup only scans its own letter.
        self.steps = []
        for variant, causes in steps:
            buckets = collections.defaultdict(list)
            for row in rows:
                cause = int(row["cause_id"])
                if row["variant"] != variant or cause not in causes:
                    continue
                for lo, hi in parse_code_list(row["icd10"]):
                    for letter in range(ord(lo[0]), ord(hi[0]) + 1):
                        buckets[chr(letter)].append((lo, hi, cause))
            self.steps.append(buckets)
        self.cache = {}

    def causes_for(self, key):
        if key not in self.cache:
            found = set()
            for buckets in self.steps:
                found = {c for lo, hi, c in buckets.get(key[:1], ()) if in_range(key, lo, hi)}
                if found:
                    break
            self.cache[key] = found
        return self.cache[key]


def assign(target, universe, index, causes):
    """Pick the GBD cause for one ICD-10 target by majority over its leaf codes."""
    votes = collections.Counter()
    for key in universe.expand(target):
        votes.update(index.causes_for(key))
    if not votes:
        return {"cause": None, "method": "none", "votes": {}}
    top = max(votes.values())
    winners = sorted((c for c, n in votes.items() if n == top), key=lambda c: causes[c]["sort"])
    if len(winners) > 1:
        return {"cause": None, "method": "tie", "candidates": winners, "votes": dict(votes)}
    return {"cause": winners[0], "method": "direct" if len(votes) == 1 else "majority", "votes": dict(votes)}


def build(provinces, who, universe, index, causes, dalys, review):
    """Cross-walk and burden for every province.

    provinces: [{uri, code, title}]; who: uri -> ICD-10 code; causes: eligible cause_id -> {name, sort};
    dalys: cause_id -> DALYs (missing = GBD models none); review: earlier review entries, possibly hand-edited.
    """
    reviewed = {e["uri"]: e for e in review}
    table, ties = {}, []
    for p in provinces:
        icd10 = who.get(p["uri"], "")
        result = assign(icd10, universe, index, causes)
        entry = {"code": p["code"], "title": p["title"], "icd10": icd10, **result}
        if result["method"] == "tie":
            prior = reviewed.get(p["uri"], {})
            resolution = prior.get("resolution", result["candidates"][0])
            if resolution is not None and resolution not in causes:
                raise ValueError(f"crosswalk-review: {p['code']} resolution {resolution} is not a GBD cause in scope")
            ties.append({
                "uri": p["uri"], "code": p["code"], "title": p["title"], "icd10": icd10,
                "candidates": [{"cause_id": c, "name": causes[c]["name"], "votes": result["votes"][c]}
                               for c in result["candidates"]],
                "resolution": resolution,
                "reviewed": bool(prior.get("reviewed", False)),
            })
            entry.update(cause=resolution, method="review", reviewed=ties[-1]["reviewed"])
        table[p["uri"]] = entry

    members = collections.defaultdict(list)
    for uri, entry in table.items():
        if entry["cause"] is not None:
            members[entry["cause"]].append(uri)
    burden = {}
    for cause, uris in members.items():
        share = dalys.get(cause, 0.0) / len(uris)
        for uri in uris:
            burden[uri] = {"dalys": share, "cause": cause, "estimated": len(uris) > 1}

    summary = {c: {"name": causes[c]["name"], "dalys": dalys.get(c), "provinces": len(members.get(c, ())),
                   **({"members": causes[c]["members"]} if "members" in causes[c] else {})}
               for c in sorted(causes, key=lambda c: causes[c]["sort"])}
    # A group's DALYs are its members', so the total counts most-detailed causes only.
    total = sum(dalys.get(c, 0.0) for c in causes if "members" not in causes[c])
    covered = sum(dalys.get(c, 0.0) for c in members)  # groups carry their members' DALYs
    mapped = sum(1 for e in table.values() if e["cause"] is not None)
    stats = {
        "provinces": len(table),
        "mapped": mapped,
        "unmapped": len(table) - mapped,
        "ties": len(ties),
        "ties_unreviewed": sum(1 for t in ties if not t["reviewed"]),
        "methods": dict(collections.Counter(e["method"] for e in table.values())),
        "mapped_without_dalys": sum(len(u) for c, u in members.items() if not dalys.get(c)),
        "causes": sum(1 for c in causes.values() if "members" not in c),
        "groups": sum(1 for c in causes.values() if "members" in c),
        "causes_covered": len(members),
        "dalys_total": total,
        "dalys_covered": covered,
        "dalys_covered_share": covered / total if total else 0.0,
    }
    return {"crosswalk": table, "review": ties, "burden": burden, "causes": summary, "stats": stats}


def report(stats, causes):
    """The stage 4 coverage report, as printed lines."""
    s = stats
    via_group = {m for c in causes.values() if c["provinces"] for m in c.get("members", ())}
    uncovered = sorted((c for cid, c in causes.items()
                        if not c["provinces"] and c["dalys"] and cid not in via_group and "members" not in c),
                       key=lambda c: -c["dalys"])
    lines = [
        f"provinces: {s['provinces']:,}",
        f"  mapped to a GBD cause: {s['mapped']:,} ({s['mapped'] / s['provinces']:.1%})"
        f"  [{', '.join(f'{k} {v:,}' for k, v in sorted(s['methods'].items()))}]",
        f"  unmapped (fog, minimum size): {s['unmapped']:,}",
        f"  ties sent to review: {s['ties']:,} ({s['ties_unreviewed']:,} still on their placeholder)",
        f"  mapped to a cause GBD gives no DALYs: {s['mapped_without_dalys']:,}",
        f"GBD causes in scope: {s['causes']} (+{s['groups']} parent groups for causes with no ICD-10 codes), "
        f"with at least one province: {s['causes_covered']}",
        f"DALYs covered: {s['dalys_covered']:,.0f} of {s['dalys_total']:,.0f} ({s['dalys_covered_share']:.1%})",
    ]
    if uncovered:
        lines.append("largest causes with no province: " +
                     "; ".join(f"{c['name']} ({c['dalys']:,.0f})" for c in uncovered[:8]))
    return lines
