"""Stage 5: MeSH search terms per GBD cause (docs/spec/v1.md, "Pipeline bar (stage 7)").

A Claude session drafts a list of MeSH headings for every GBD cause into git-ignored data/raw/stage5-drafts/
(runbook: pipeline/STAGE5.md; the owner chose a session over the Claude API on 2026-10-29). This stage resolves
each heading to its descriptor ID through NLM's lookup API (current MeSH, or the year ClinicalTrials.gov uses) and
writes data/mesh.yaml. Headings should be the labels ClinicalTrials.gov indexes trials under:

    493:
      cause: Ischemic heart disease
      terms: {D003324: Coronary Artery Disease, D017202: Myocardial Ischemia}
      reviewed: false

The owner reviews each entry and sets `reviewed: true`; stage 7 searches ClinicalTrials.gov with reviewed terms
only. Re-runs never touch a reviewed entry; unreviewed ones follow the current drafts. A draft with an unknown
heading is rejected (and any older entry kept) until it's fixed.
"""
import yaml

HEADER = """# Stage 5 MeSH search terms per GBD cause (docs/spec/v1.md), drafted by a Claude session (pipeline/STAGE5.md).
# Review each entry: edit `terms` (descriptor ID: exact MeSH heading), then set `reviewed: true`.
# Stage 7 searches ClinicalTrials.gov with reviewed entries only. Re-runs of stage 5 keep reviewed entries and
# rewrite the rest from the drafts, so mark an entry reviewed to keep your edits.
"""


def causes(burden):
    """Every GBD cause in burden.json, groups and causes without provinces included, biggest burden first."""
    out = [{"id": int(cid), "name": c["name"], "dalys": c["dalys"] or 0} for cid, c in burden["causes"].items()]
    return sorted(out, key=lambda c: (-c["dalys"], c["id"]))


def build(cause_list, drafts, existing, mesh_id):
    """-> (entries {cause id: entry} in cause order, problems {cause id: [reason]}).
    mesh_id(heading) -> descriptor ID or None."""
    entries, problems = {}, {}
    for cause in cause_list:
        cid, old = cause["id"], existing.get(cause["id"])
        if old and old.get("reviewed") is True:
            entries[cid] = old
            continue
        headings = drafts.get(cid)
        if headings is None:
            reasons = ["no draft"]
        elif not headings:
            reasons = ["needs at least one MeSH heading"]
        else:
            ids = {h: mesh_id(h) for h in headings}
            reasons = [f"MeSH heading not found: {h}" for h, i in ids.items() if not i]
        if reasons:
            problems[cid] = reasons
            if old:
                entries[cid] = old
            continue
        entries[cid] = {"cause": cause["name"], "terms": {i: h for h, i in ids.items()}, "reviewed": False}
    return entries, problems


def first_found(*lookups):
    """mesh_id(heading) trying each lookup in turn. Stage 5 asks current MeSH, then the year ClinicalTrials.gov
    indexes conditions with, whose labels can differ (2026 renamed "Depressive Disorder, Major" to "Major
    Depressive Disorder", but trials are still indexed under the old label)."""
    def resolve(heading):
        return next((i for i in (lookup(heading) for lookup in lookups) if i), None)
    return resolve


def reviewed_terms(entries):
    """cause id -> {descriptor ID: heading}, for reviewed entries only."""
    return {cid: e["terms"] for cid, e in entries.items() if e.get("reviewed") is True and e.get("terms")}


def read(path):
    if not path.exists():
        return {}
    return {int(k): v for k, v in (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).items()}


def write(path, entries):
    path.write_text(HEADER + yaml.safe_dump(entries, sort_keys=False, allow_unicode=True, width=120),
                    encoding="utf-8", newline="\n")


def read_drafts(folder):
    """cause id -> [MeSH headings], from every YAML file in the folder."""
    out = {}
    for path in sorted(folder.glob("*.yaml")):
        out.update({int(k): v for k, v in (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).items()})
    return out
