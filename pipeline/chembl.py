"""ChEMBL approved-drug indications (drug_indication rows with max_phase_for_ind = 4), via the REST API.

Saved into git-ignored data/raw/chembl/ with the release from status.json. ChEMBL is CC BY-SA 3.0: cite
Mendez D et al., Nucleic Acids Res. 2019;47(D1):D930-D940, doi:10.1093/nar/gky1075, and show the release.
"""
import json
import time
import urllib.request

API = "https://www.ebi.ac.uk/chembl/api/data/"
FIELDS = "mesh_id,mesh_heading,max_phase_for_ind,parent_molecule_chembl_id"


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"Accept": "application/json"}), timeout=60) as r:
        return json.load(r)


def fetch(raw_dir, page_size=1000):
    """Write raw_dir/drug_indication.json: {release, release_date, fetched, rows}."""
    status = get(API + "status.json")
    rows, url = [], f"{API}drug_indication.json?max_phase_for_ind=4&limit={page_size}&only={FIELDS}"
    while url:
        page = get(url)
        rows += page["drug_indications"]
        nxt = page["page_meta"]["next"]
        url = "https://www.ebi.ac.uk" + nxt if nxt else None
        time.sleep(0.5)
    raw_dir.mkdir(parents=True, exist_ok=True)
    out = {"release": status["chembl_db_version"], "release_date": status["chembl_release_date"],
           "fetched": time.strftime("%Y-%m-%d"), "rows": rows}
    (raw_dir / "drug_indication.json").write_text(json.dumps(out, indent=0) + "\n", encoding="utf-8")
    print(f"  {out['release']}: {len(rows)} approved indication rows")
