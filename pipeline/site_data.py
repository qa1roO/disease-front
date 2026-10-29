"""Stage 8: build site/public/map.json, everything the front end needs, from the earlier stages.

For now (ticket 02) only the tree exists: every province has the same size and is fog (status null).
"""


def build_map(tree):
    def node(n):
        out = {"kind": n["kind"], "code": n["code"], "title": n["title"], "uri": n["uri"]}
        if "children" in n:
            out["children"] = [node(c) for c in n["children"]]
        else:
            out["size"] = 1
            out["status"] = None
        return out

    return {
        "meta": {"icd11": tree["icd11"], "counts": tree["counts"]},
        "root": {"kind": "root", "title": "All diseases", "children": [node(c) for c in tree["chapters"]]},
    }
