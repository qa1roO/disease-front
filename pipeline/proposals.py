"""Stage 6: status proposals for the non-communicable GBD causes (docs/spec/v1.md, "Status proposals and review").

A proposer (Claude with web search) drafts a status 1-5 per cause, with a nuance note, sources and the MeSH
descriptors the cross-check uses. Each proposal is checked before it's written to data/proposals/:

- every source URL must resolve (HTTP 200), or the proposal is rejected and the proposer retried with the reason;
- the ChEMBL cross-check flags a status that disagrees with the approved-drug data (Curable or Controlled with no
  approved drug, Untreatable with one). Flags are for the owner's review; they don't block the file.

The owner reviews each file and flips `approved: true`. A re-run keeps every existing file; with `refresh` it
regenerates only the ones that are neither approved nor edited (the fingerprint covers the reviewable fields).
Only approved proposals reach map.json, and each approval that changes a cause's status appends an event to
data/events.json.

Cross-check flags derive from ChEMBL (CC BY-SA 3.0), so the proposal files are share-alike too.
"""
import hashlib
import re
import urllib.error
import urllib.request

import yaml

NCD = "Non-communicable diseases"
TRIES = 3
STATUS_NAME = {1: "Eradicated", 2: "Curable", 3: "Controlled", 4: "Treatable", 5: "Untreatable"}
REVIEWABLE = ("status", "nuance", "sources", "mesh")
HEADER = """# Stage 6 status proposal (docs/spec/v1.md). Review it, edit freely, then set `approved: true`.
# Re-runs never overwrite an approved or edited file. cross_check derives from ChEMBL (CC BY-SA 3.0).
"""


def ncd_causes(burden):
    """The non-communicable GBD causes that have provinces on the map, biggest burden first."""
    causes = burden["causes"]
    out = [{"id": int(cid), "name": c["name"], "dalys": c["dalys"] or 0,
            "members": [causes[str(m)]["name"] for m in c.get("members", [])]}
           for cid, c in causes.items() if c.get("group") == NCD and c["provinces"] > 0]
    return sorted(out, key=lambda c: (-c["dalys"], c["id"]))


def file_name(cause):
    slug = re.sub(r"[^a-z0-9]+", "-", cause["name"].lower()).strip("-")
    return f"{cause['id']}-{slug}.yaml"


def approved_drugs(rows):
    """MeSH ID -> sorted parent molecule ChEMBL IDs, from ChEMBL drug_indication rows at max_phase_for_ind 4."""
    out = {}
    for r in rows:
        if r.get("mesh_id") and float(r.get("max_phase_for_ind") or 0) == 4:
            out.setdefault(r["mesh_id"], set()).add(r["parent_molecule_chembl_id"])
    return {k: sorted(v) for k, v in sorted(out.items())}


def cross_check(proposal, approved):
    status, mesh = proposal["status"], proposal.get("mesh") or []
    hits = {m: approved[m] for m in mesh if m in approved}
    name = STATUS_NAME.get(status, status)
    if status in (2, 3) and not hits:
        terms = ", ".join(mesh) or "no MeSH terms given"
        return f"flag: claims {name} but ChEMBL has no approved drug ({terms})"
    if status == 5 and hits:
        drugs = sorted({d for v in hits.values() for d in v})
        return f"flag: claims {name} but ChEMBL has {len(drugs)} approved drug{'s' * (len(drugs) != 1)} for {', '.join(hits)}"
    return "ok"


def resolves(url, opener=None):
    """True when the URL answers HTTP 200 (after redirects). Servers that refuse HEAD get a GET."""
    if not re.match(r"https?://", url or ""):
        return False
    opener = opener or http_status
    try:
        status = opener(url, "HEAD")
        if status != 200:
            status = opener(url, "GET")
        return status == 200
    except Exception:
        return False


def http_status(url, method):
    request = urllib.request.Request(url, method=method, headers={
        "User-Agent": "Mozilla/5.0 (disease-map source check; +https://github.com/qa1roO/disease-front)",
        "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status
    except urllib.error.HTTPError as e:
        return e.code


def problems(proposal, check_url):
    out = []
    status = proposal.get("status")
    if not isinstance(status, int) or isinstance(status, bool) or not 1 <= status <= 5:
        out.append(f"status must be an integer 1-5, got {status!r}")
    sources = proposal.get("sources") or []
    if not sources:
        out.append("needs at least one source")
    for s in sources:
        if not s.get("url"):
            out.append(f"source has no url: {s}")
        elif not check_url(s["url"]):
            out.append(f"source does not resolve: {s['url']}")
    return out


def fingerprint(proposal):
    reviewable = {k: proposal.get(k) for k in REVIEWABLE}
    return hashlib.sha256(yaml.safe_dump(reviewable, sort_keys=True).encode()).hexdigest()[:16]


def untouched(proposal):
    return not proposal.get("approved") and proposal.get("fingerprint") == fingerprint(proposal)


def read(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write(path, proposal):
    path.write_text(HEADER + yaml.safe_dump(proposal, sort_keys=False, allow_unicode=True, width=110),
                    encoding="utf-8", newline="\n")


def build(cause, draft, approved):
    out = {"gbd_cause": cause["name"], "gbd_cause_id": cause["id"], "status": draft["status"],
           "nuance": draft.get("nuance") or "", "sources": draft["sources"], "mesh": draft.get("mesh") or []}
    out["cross_check"] = cross_check(out, approved)
    out["approved"] = False
    out["fingerprint"] = fingerprint(out)
    return out


def run(causes, folder, propose, check_url, approved, refresh=False, log=print):
    """Propose a status for each cause. propose(cause, feedback) returns {status, nuance, sources, mesh}."""
    folder.mkdir(parents=True, exist_ok=True)
    result = {"written": [], "kept": [], "failed": {}, "flagged": {}}
    for cause in causes:
        path = folder / file_name(cause)
        if path.exists() and not (refresh and untouched(read(path))):
            result["kept"].append(cause["id"])
            continue
        feedback = []
        for _ in range(TRIES):
            draft = propose(cause, feedback)
            feedback = problems(draft, check_url)
            if not feedback:
                write(path, build(cause, draft, approved))
                result["written"].append(cause["id"])
                log(f"  {cause['id']} {cause['name']}: {STATUS_NAME[draft['status']]}")
                break
        else:
            result["failed"][cause["id"]] = feedback
            log(f"  {cause['id']} {cause['name']}: rejected after {TRIES} tries: {'; '.join(feedback)}")
    for cause in causes:
        path = folder / file_name(cause)
        if path.exists() and (p := read(path))["cross_check"] != "ok":
            result["flagged"][cause["id"]] = p["cross_check"]
    write_index(causes, folder)
    return result


def write_index(causes, folder):
    """data/proposals/INDEX.md: one line per cause, so flagged and unapproved proposals are easy to find."""
    lines = ["# Status proposals", "",
             "Generated by stage 6. FLAG = the ChEMBL cross-check disagrees; review those first.", "",
             "| Cause | Status | Approved | Cross-check | File |", "|---|---|---|---|---|"]
    for cause in causes:
        path = folder / file_name(cause)
        if not path.exists():
            lines.append(f"| {cause['name']} | missing | | | |")
            continue
        p = read(path)
        check = "ok" if p["cross_check"] == "ok" else "**FLAG** " + p["cross_check"].removeprefix("flag: ")
        lines.append(f"| {p['gbd_cause']} | {p['status']} {STATUS_NAME.get(p['status'], '')} | "
                     f"{'yes' if p.get('approved') else 'no'} | {check} | [{path.name}]({path.name}) |")
    (folder / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def load_approved(folder):
    """cause_id -> proposal, for every approved proposal in the folder."""
    out = {}
    for path in sorted(folder.glob("*.yaml")):
        p = read(path)
        if p.get("approved") is True:
            out[int(p["gbd_cause_id"])] = p
    return out


def record_events(approved, events, date):
    """Append {date, cause, name, from, to} for every approved status that differs from the last one recorded."""
    current = {}
    for e in events:
        current[e["cause"]] = e["to"]
    new = list(events)
    for cid in sorted(approved):
        status = approved[cid]["status"]
        if current.get(cid) != status:
            new.append({"date": date, "cause": cid, "name": approved[cid]["gbd_cause"],
                        "from": current.get(cid), "to": status})
    return new
