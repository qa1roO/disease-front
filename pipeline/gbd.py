"""Reading the GBD 2023 files that stage 2 saves into data/raw/gbd/ (see pipeline/STAGE2.md).

Stage 2 runs from a Claude session, because the IHME GBD MCP connector works only inside Claude.
The raw files stay git-ignored: IHME forbids rehosting them (docs/research/data-sources.md, section 3).
"""
import csv
import io

ROUND = "GBD 2023"
CITATION = "Source: Institute for Health Metrics and Evaluation. Used with permission. All rights reserved."
# Flagged most_detailed but published totals that overlap the ordinary hierarchy: counting them double-counts.
AGGREGATES = {1026, 1027, 1028, 1029, 1059}
INJURIES = 687


def rows(text):
    return list(csv.DictReader(io.StringIO(text.lstrip("﻿"))))


def causes_in_scope(hierarchy_csv):
    """cause_id -> {name, sort, group} for every most-detailed disease cause (level 3 or 4), minus injuries."""
    table = {int(r["cause_id"]): r for r in rows(hierarchy_csv)}

    def ancestors(r):
        while r:
            yield r
            r = table.get(int(r["parent_id"]))

    out = {}
    for cid, r in table.items():
        if r["most_detailed"] != "1" or cid in AGGREGATES or r["level"] not in ("3", "4"):
            continue
        chain = list(ancestors(r))
        if any(int(a["cause_id"]) == INJURIES for a in chain):
            continue
        out[cid] = {"name": r["cause_name"], "sort": float(r["sort_order"]), "group": chain[-1]["cause_name"]}
    return out


def dalys(level3_csv, level4_csv):
    """cause_id -> global DALYs, 2023, all ages, both sexes (count_combined)."""
    return {int(r["cause_id"]): float(r["count_combined"]) for text in (level3_csv, level4_csv) for r in rows(text)}


# Rows of the cause -> ICD map that carry no cause_id but hold the codes of a reporting cause in scope.
INTERNAL = {
    "Other direct maternal disorders (internal)": 1160,
    "Other digestive diseases (internal)": 1161,
    "Diverticular disease of intestines": 1161,
    "Other benign and in situ neoplasms (internal)": 1164,
    "Non-malignant brain and other central nervous system neoplasms": 1164,
}


def icd_rows(icd_csv, extra):
    """GBD's cause -> ICD-10 lists as {cause_id, variant, icd10}, internal rows named, plus the project's own
    codes (data/gbd-extra-codes.yaml) as variant 'project'. Rows with no cause (garbage codes, notes) are dropped."""
    out = []
    for r in rows(icd_csv):
        cause = r["cause_id"] or INTERNAL.get(r["cause_name"])
        codes = r["icd10"].strip()
        if cause and codes and codes != "N/A":
            out.append({"cause_id": str(cause), "variant": r["variant"], "icd10": codes})
    out += [{"cause_id": str(e["cause_id"]), "variant": "project", "icd10": e["icd10"]} for e in extra]
    return out


def groups(hierarchy_csv, icd, in_scope):
    """Causes in scope with no ICD-10 codes at all fold into their nearest level-2 or level-3 ancestor that has
    codes: GBD splits them out of that parent by modelling (etiologies, subtypes). Returns ancestor cause_id ->
    {name, sort, group, level, members}; its DALYs are its members' sum."""
    table = {int(r["cause_id"]): r for r in rows(hierarchy_csv)}
    coded = {int(r["cause_id"]) for r in icd}
    out = {}
    for cid in sorted(in_scope, key=lambda c: in_scope[c]["sort"]):
        if cid in coded:
            continue
        parent = table.get(int(table[cid]["parent_id"]))
        while parent and parent["level"] in ("2", "3") and int(parent["cause_id"]) not in coded:
            parent = table.get(int(parent["parent_id"]))
        if not parent or parent["level"] not in ("2", "3"):
            continue
        pid = int(parent["cause_id"])
        out.setdefault(pid, {"name": parent["cause_name"], "sort": float(parent["sort_order"]),
                             "group": in_scope[cid]["group"], "level": int(parent["level"]), "members": []})
        out[pid]["members"].append(cid)
    return out
