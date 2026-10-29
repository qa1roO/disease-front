"""Stage 7: the pipeline bar per GBD cause (docs/spec/v1.md, "Pipeline bar (stage 7)").

For each cause with reviewed MeSH terms (stage 5), ClinicalTrials.gov API v2 is asked how many interventional
trials that are still running (recruiting, not yet recruiting, enrolling by invitation, or active and not
recruiting), and were first posted in the 10 years before the API's data date, have one of those terms as a
condition. Completed trials don't count: the bar shows the progress still being made against the cause. It is the
furthest phase among those trials:

- Phase 3 (Phase 4 post-approval trials count here: the drug got past Phase 3), Phase 2, Phase 1 (Early Phase 1
  counts as Phase 1);
- "none" (No registered trial) otherwise. Phase "NA" trials (devices, behavioural) count as trials but set no
  phase, and the registry can't show preclinical work.

The bar is never Approved here. Approved belongs to held provinces (status 1-3), set in stage 8. The owner decided
this on 2026-10-29: ChEMBL's approved-drug data made most contested causes read Approved, which said nothing about
progress.

Each cause costs one request for the trial count, plus one per phase, highest first, until one has trials.
Requests are spaced 1 s apart (no limit is published; third-party guides report ~50/min) and back off on HTTP 429
and 5xx. Counts are cached in git-ignored data/raw/ctgov-counts.json per API dataTimestamp, so an interrupted run
resumes and a re-run on the same data asks nothing.
"""
import datetime
import json
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://clinicaltrials.gov/api/v2/"
WEBSITE = "https://clinicaltrials.gov/search"
STATUSES = "RECRUITING|NOT_YET_RECRUITING|ENROLLING_BY_INVITATION|ACTIVE_NOT_RECRUITING"
WEBSITE_STATUSES = "rec not enr act"  # the website's codes for the same four statuses
TIERS = [("phase3", "(PHASE3 OR PHASE4)"), ("phase2", "PHASE2"), ("phase1", "(PHASE1 OR EARLY_PHASE1)")]
YEARS = 10
# The MeSH year whose labels ClinicalTrials.gov indexes conditions under (checked 2026-10-29: "Depressive
# Disorder, Major" finds 2,966 trials, its 2026 label "Major Depressive Disorder" 5).
CTGOV_MESH_YEAR = 2025
NOTE = ("Pipeline bar per GBD cause: the furthest phase among interventional ClinicalTrials.gov trials still running "
        "(recruiting, not yet recruiting, enrolling by invitation, or active and not recruiting; completed trials don't "
        "count), first posted since registeredSince, whose conditions include one of the cause's reviewed MeSH terms "
        "(data/mesh.yaml). Phase 4 counts as Phase 3. Held provinces (status 1-3) show Approved instead, set in stage 8. "
        "Derived from ClinicalTrials.gov.")


def since(data_timestamp):
    """The date YEARS before the API's data date (Feb 29 falls back to Feb 28)."""
    d = datetime.date.fromisoformat(data_timestamp[:10])
    try:
        return d.replace(year=d.year - YEARS).isoformat()
    except ValueError:
        return d.replace(year=d.year - YEARS, day=28).isoformat()


def condition(terms):
    return " OR ".join(f'AREA[ConditionMeshTerm]"{h}"' for h in terms.values())


def params(terms, since_date, phase=None):
    advanced = f"AREA[StudyType]INTERVENTIONAL AND AREA[StudyFirstPostDate]RANGE[{since_date},MAX]"
    if phase:
        advanced += f" AND AREA[Phase]{phase}"
    return {"query.cond": condition(terms), "filter.overallStatus": STATUSES, "filter.advanced": advanced,
            "countTotal": "true", "pageSize": "1", "fields": "NCTId"}


def search_url(terms, since_date):
    """The same search (all phases) on the ClinicalTrials.gov website; its phase filter shows the breakdown."""
    query = {"cond": condition(terms), "aggFilters": f"status:{WEBSITE_STATUSES},studyType:int",
             "firstPost": f"{since_date}_"}
    return WEBSITE + "?" + urllib.parse.urlencode(query, quote_via=urllib.parse.quote)


def bar(terms, count, since_date):
    """{phase, trials, url} for one cause. count(params) -> totalCount."""
    out = {"phase": "none", "trials": count(params(terms, since_date)), "url": search_url(terms, since_date)}
    if out["trials"]:
        out["phase"] = next((name for name, phase in TIERS if count(params(terms, since_date, phase))), "none")
    return out


def run(cause_terms, count, since_date, log=lambda line: None):
    """cause id -> {cause's reviewed terms}, to {str(cause id): bar}."""
    out = {}
    for cid, terms in cause_terms.items():
        out[str(cid)] = bar(terms, count, since_date)
        log(f"  {cid}: {out[str(cid)]['phase']}, {out[str(cid)]['trials']} trials")
    return out


class Polite:
    """Wraps get(url): spaces calls `interval` seconds apart and retries HTTP 429 / 5xx / network errors, waiting
    Retry-After when given, else backoff, 2 x backoff, ..."""

    def __init__(self, get, interval=1.0, backoff=5.0, tries=6, clock=time.monotonic, sleep=time.sleep):
        self.get, self.interval, self.backoff, self.tries = get, interval, backoff, tries
        self.clock, self.sleep, self.last = clock, sleep, None

    def __call__(self, url):
        wait = self.backoff
        for attempt in range(self.tries):
            if self.last is not None and (gap := self.interval - (self.clock() - self.last)) > 0:
                self.sleep(gap)
            self.last = self.clock()
            try:
                return self.get(url)
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
                code = getattr(e, "code", None)
                if code is not None and code != 429 and code < 500 or attempt == self.tries - 1:
                    raise
                retry_after = e.headers.get("Retry-After") if code else None
                pause = float(retry_after) if retry_after and retry_after.isdigit() else wait
                wait *= 2
                self.sleep(pause)
                self.last = None  # the back-off already spaced this retry


def get_json(url):
    request = urllib.request.Request(url, headers={
        "Accept": "application/json", "User-Agent": "disease-map pipeline (+https://github.com/qa1roO/disease-front)"})
    with urllib.request.urlopen(request, timeout=60) as r:
        return json.load(r)


def api_counter(get):
    """count(params) -> totalCount, over get(url) -> parsed JSON."""
    return lambda p: get(API + "studies?" + urllib.parse.urlencode(p))["totalCount"]


def cache_key(p):
    return urllib.parse.urlencode(sorted(p.items()))


class CountCache:
    """count(params) memoised in data {dataTimestamp, counts}; save(data) after each new count. A cache from an
    older dataTimestamp is dropped."""

    def __init__(self, data, data_timestamp, count, save=lambda data: None):
        if data.get("dataTimestamp") != data_timestamp:
            data = {"dataTimestamp": data_timestamp, "counts": {}}
        self.data, self.count, self.save = data, count, save

    def __call__(self, p):
        key = cache_key(p)
        if key not in self.data["counts"]:
            self.data["counts"][key] = self.count(p)
            self.save(self.data)
        return self.data["counts"][key]
