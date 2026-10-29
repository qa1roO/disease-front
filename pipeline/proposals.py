"""Stage 6: status proposals for the non-communicable GBD causes (docs/spec/v1.md, "Status proposals and review").

A Claude session with web search drafts a status 1-5 per GBD cause on the map (every group: non-communicable,
communicable, maternal, neonatal and nutritional), or per ICD-11 disease for a direct assessment (e.g. smallpox,
which no GBD cause covers), with a nuance note, sources and the MeSH headings
the cross-check uses, into git-ignored data/raw/stage6-drafts/ (runbook: pipeline/STAGE6.md). This stage resolves
the headings to MeSH descriptor IDs and checks each draft before it's written to data/proposals/:

- every source URL must resolve (HTTP 200) and every MeSH heading must exist, or the draft is rejected with the
  reason, to be fixed in the session and re-run;
- the ChEMBL cross-check flags a status that disagrees with the approved-drug data (Curable or Controlled with no
  approved drug, Untreatable with one). Flags are for the owner's review; they don't block the file.

The owner reviews each file and flips `approved: true`. A re-run keeps every existing file; with `refresh` it
regenerates only the ones that are neither approved nor edited (the fingerprint covers the reviewable fields).
Only approved proposals reach map.json, and each approval that changes a cause's status appends an event to
data/events.json.

Cross-check flags derive from ChEMBL (CC BY-SA 3.0), so the proposal files are share-alike too.
"""
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

import yaml

TRIES = 3
STATUS_NAME = {1: "Eradicated", 2: "Curable", 3: "Controlled", 4: "Treatable", 5: "Untreatable"}
REVIEWABLE = ("status", "nuance", "sources", "mesh")
HEADER = """# Stage 6 status proposal (docs/spec/v1.md). Review it, edit freely, then set `approved: true`.
# Re-runs never overwrite an approved or edited file. cross_check derives from ChEMBL (CC BY-SA 3.0).
"""


def causes_on_map(burden):
    """The GBD causes that have provinces on the map, biggest burden first."""
    causes = burden["causes"]
    out = [{"id": int(cid), "name": c["name"], "dalys": c["dalys"] or 0,
            "members": [causes[str(m)]["name"] for m in c.get("members", [])]}
           for cid, c in causes.items() if c["provinces"] > 0]
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


def resolves(url, opener=None, pause=3.0):
    """True when the URL answers HTTP 200 (after redirects). Servers that refuse HEAD get a GET. Network errors,
    403, 429 and 5xx get one more try after a pause, since busy government sites drop the odd request."""
    if not re.match(r"https?://", url or ""):
        return False
    opener = opener or http_status
    for attempt in range(2):
        try:
            status = opener(url, "HEAD")
            if status != 200:
                status = opener(url, "GET")
        except Exception:
            status = None
        if status == 200 or status not in (None, 403, 429) and status < 500:
            return status == 200
        if attempt == 0:
            time.sleep(pause)
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
    out += [f"MeSH heading not found: {h}" for h in proposal.get("unresolved_mesh", [])]
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


def identity(subject):
    """The fields that say what a proposal is about: a GBD cause, or an ICD-11 disease (subject["identity"])."""
    return subject.get("identity") or {"gbd_cause": subject["name"], "gbd_cause_id": subject["id"]}


def build(cause, draft, approved):
    out = {**identity(cause), "status": draft["status"], "nuance": draft.get("nuance") or "",
           "sources": draft["sources"], "mesh": draft.get("mesh") or []}
    out["cross_check"] = cross_check(out, approved)
    out["approved"] = False
    out["fingerprint"] = fingerprint(out)
    return out


def read_drafts(folder):
    """cause_id (or ICD-11 code) -> draft {status, nuance, sources, mesh: [MeSH headings]}, from every YAML file in
    the folder."""
    out = {}
    for path in sorted(folder.glob("*.yaml")):
        out.update({int(k) if str(k).isdigit() else str(k): v for k, v in (read(path) or {}).items()})
    return out


def draft_proposer(drafts, mesh_id):
    """A propose(cause, feedback) over session-written drafts. mesh_id(heading) -> descriptor ID or None."""
    def propose(cause, feedback):
        if cause["id"] not in drafts:
            return None
        draft = dict(drafts[cause["id"]])
        headings = draft.get("mesh") or []
        ids = {h: mesh_id(h) for h in headings}
        draft["mesh"] = {i: h for h, i in ids.items() if i}
        draft["unresolved_mesh"] = [h for h, i in ids.items() if not i]
        return draft
    return propose


class MeshLookup:
    """MeSH heading -> descriptor ID via NLM's lookup API (exact label match), cached in a JSON file."""

    def __init__(self, cache_path):
        self.path = cache_path
        self.cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}

    def __call__(self, heading):
        if heading not in self.cache:
            url = ("https://id.nlm.nih.gov/mesh/lookup/descriptor?match=exact&limit=1&label="
                   + urllib.parse.quote(heading))
            with urllib.request.urlopen(url, timeout=30) as r:
                hits = json.load(r)
            self.cache[heading] = hits[0]["resource"].rsplit("/", 1)[1] if hits else None
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.cache, indent=0, sort_keys=True), encoding="utf-8")
        return self.cache[heading]


def run(causes, folder, propose, check_url, approved, refresh=False, tries=TRIES, log=print):
    """Propose a status for each cause. propose(cause, feedback) returns {status, nuance, sources, mesh}, or None
    when it has nothing for the cause."""
    folder.mkdir(parents=True, exist_ok=True)
    result = {"written": [], "kept": [], "failed": {}, "flagged": {}}
    for cause in causes:
        path = folder / file_name(cause)
        if path.exists() and not (refresh and untouched(read(path))):
            result["kept"].append(cause["id"])
            continue
        feedback = []
        for _ in range(tries):
            draft = propose(cause, feedback)
            feedback = ["no draft"] if draft is None else problems(draft, check_url)
            if not feedback:
                write(path, build(cause, draft, approved))
                result["written"].append(cause["id"])
                log(f"  {cause['id']} {cause['name']}: {STATUS_NAME[draft['status']]}")
                break
            if draft is None:
                break
        if feedback:
            result["failed"][cause["id"]] = feedback
            log(f"  {cause['id']} {cause['name']}: rejected: {'; '.join(feedback)}")
    for cause in causes:
        path = folder / file_name(cause)
        if path.exists() and (p := read(path))["cross_check"] != "ok":
            result["flagged"][cause["id"]] = p["cross_check"]
    write_index(causes, folder)
    return result


def write_index(causes, folder):
    """INDEX.md: one line per cause or disease, so flagged and unapproved proposals are easy to find."""
    lines = ["# Status proposals", "",
             "Generated by stage 6. FLAG = the ChEMBL cross-check disagrees; review those first.", "",
             "| Subject | Status | Approved | Cross-check | File |", "|---|---|---|---|---|"]
    for cause in causes:
        path = folder / file_name(cause)
        if not path.exists():
            lines.append(f"| {cause['name']} | missing | | | |")
            continue
        p = read(path)
        check = "ok" if p["cross_check"] == "ok" else "**FLAG** " + p["cross_check"].removeprefix("flag: ")
        lines.append(f"| {p.get('gbd_cause') or p.get('icd11_title')} | {p['status']} {STATUS_NAME.get(p['status'], '')} | "
                     f"{'yes' if p.get('approved') else 'no'} | {check} | [{path.name}]({path.name}) |")
    (folder / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def load_approved(folder, key="gbd_cause_id"):
    """proposal[key] (cause id, or ICD-11 URI for direct assessments) -> proposal, for every approved one."""
    out = {}
    for path in sorted(folder.glob("*.yaml")):
        p = read(path)
        if p.get("approved") is True:
            out[int(p[key]) if key == "gbd_cause_id" else p[key]] = p
    return out


def record_events(approved, events, date, field="cause", name_field="gbd_cause"):
    """Append {date, <field>, name, from, to} for every approved status that differs from the last one recorded.
    field is "cause" (GBD cause id) or "icd11" (ICD-11 code, for direct assessments)."""
    current = {}
    for e in events:
        if field in e:
            current[e[field]] = e["to"]
    new = list(events)
    for cid in sorted(approved):
        status = approved[cid]["status"]
        if current.get(cid) != status:
            new.append({"date": date, field: cid, "name": approved[cid][name_field],
                        "from": current.get(cid), "to": status})
    return new
