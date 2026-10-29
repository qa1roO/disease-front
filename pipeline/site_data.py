"""Stage 8: build site/public/map.json, everything the front end needs, from the earlier stages.

A province's size is its burden in DALYs (stage 4), 0 when no GBD cause covers it (the front end then gives it
the minimum size). A province under a GBD cause with an approved stage-6 proposal inherits its status as
provisional; every other province is fog (status null). The cause's assessment (status, nuance, sources,
cross-check) sits once in meta.gbdCauses. A directly assessed province (approved, keyed by ICD-11 URI) takes its
own status instead, not provisional, with its assessment inline; that works for provinces with no GBD cause too.

The pipeline bar (stage 7) sits once per cause in meta.gbdCauses[cause].bar; each province carries its phase as
`pipeline`, inherited from its cause, or "approved" when the province is held (status 1-3).
"""


def build_map(tree, crosswalk, burden, approved=None, assessed=None, bars=None):
    approved, assessed = approved or {}, assessed or {}
    cause_bars = (bars or {}).get("causes", {})
    table, sizes = crosswalk["provinces"], burden["provinces"]
    on_map = {str(b["cause"]) for b in sizes.values()}

    def cause(v):
        # A group (a GBD parent standing in for sub-causes with no ICD-10 codes) names its members.
        out = {k: v[k] for k in ("name", "dalys", "provinces")}
        if "members" in v:
            out["members"] = [burden["causes"][str(m)]["name"] for m in v["members"]]
        return out

    def assessment(p):
        return {"status": p["status"], "nuance": p.get("nuance") or "", "sources": p["sources"],
                "crossCheck": p.get("cross_check", "ok")}

    def node(n):
        out = {"kind": n["kind"], "code": n["code"], "title": n["title"], "uri": n["uri"]}
        if "children" in n:
            out["children"] = [node(c) for c in n["children"]]
            return out
        b = sizes.get(n["uri"])
        out["size"] = round(b["dalys"], 1) if b else 0
        out["status"] = None
        if n["uri"] in assessed:
            own = assessed[n["uri"]]
            out["status"], out["provisional"], out["assessment"] = own["status"], False, assessment(own)
        elif b and b["cause"] in approved:
            out["status"], out["provisional"] = approved[b["cause"]]["status"], True
        if b:
            entry = table[n["uri"]]
            out["burden"] = {"dalys": round(b["dalys"], 1), "estimated": b["estimated"], "cause": b["cause"],
                             "method": entry["method"], "icd10": entry["icd10"]}
            if entry["method"] == "review":
                out["burden"]["reviewed"] = entry["reviewed"]
        if out["status"] is not None and out["status"] <= 3:
            out["pipeline"] = "approved"
        elif b and str(b["cause"]) in cause_bars:
            out["pipeline"] = cause_bars[str(b["cause"])]["phase"]
        return out

    meta_bars = {"clinicaltrials": bars["source"]} if bars else {}
    return {
        "meta": {
            "icd11": tree["icd11"],
            "counts": tree["counts"],
            "gbd": burden["gbd"],
            "crosswalk": crosswalk["note"],
            "gbdCauses": {c: {**cause(v), **({"assessment": assessment(approved[int(c)])} if int(c) in approved else {}),
                              **({"bar": cause_bars[c]} if c in cause_bars else {})}
                          for c, v in burden["causes"].items() if c in on_map},
            **meta_bars,
        },
        "root": {"kind": "root", "title": "All diseases", "children": [node(c) for c in tree["chapters"]]},
    }
