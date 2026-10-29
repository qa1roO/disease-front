import unittest

from pipeline import icd11, site_data, tree
from tests.pipeline.fixtures import TABULATION
from tests.pipeline.test_tree import walk

GBD = {"round": "GBD 2023", "released": "2025-10", "estimateYear": 2023, "fetched": "2026-10-29",
       "measure": "DALYs", "citation": "Source: IHME."}


def provinces(node):
    return [n for n in walk(node) if "children" not in n and n.get("kind") != "root"]


class BuildMapTest(unittest.TestCase):
    def setUp(self):
        self.tree = tree.build_tree(icd11.parse_tabulation(TABULATION), version="test")
        uris = [p["uri"] for c in self.tree["chapters"] for p in provinces(c)]
        self.cholera, self.coli, self.quoted, self.brain = uris
        self.crosswalk = {"note": "Project-made cross-walk.", "provinces": {
            self.cholera: {"cause": 302, "method": "direct", "icd10": "A00.9"},
            self.coli: {"cause": 302, "method": "majority", "icd10": "A04"},
            self.quoted: {"cause": None, "method": "none", "icd10": "No Mapping"},
            self.brain: {"cause": 417, "method": "review", "icd10": "C71", "reviewed": False},
        }}
        self.burden = {"gbd": GBD, "stats": {"dalys_covered_share": 0.9},
                       "causes": {"302": {"name": "Diarrheal diseases", "dalys": 1000.4, "provinces": 2},
                                  "417": {"name": "Liver cancer", "dalys": 50.0, "provinces": 1, "members": [418]},
                                  "418": {"name": "Liver cancer due to hepatitis B", "dalys": 50.0, "provinces": 0},
                                  "999": {"name": "Not on the map", "dalys": 7.0, "provinces": 0}},
                       "provinces": {self.cholera: {"dalys": 500.2, "cause": 302, "estimated": True},
                                     self.coli: {"dalys": 500.2, "cause": 302, "estimated": True},
                                     self.brain: {"dalys": 50.0, "cause": 417, "estimated": False}}}
        self.map = site_data.build_map(self.tree, self.crosswalk, self.burden)
        self.nodes = list(walk(self.map["root"]))[1:]
        self.by_uri = {n["uri"]: n for n in self.nodes}

    def test_root_holds_the_chapters(self):
        self.assertEqual([c["code"] for c in self.map["root"]["children"]], ["01", "02"])

    def test_province_size_is_its_burden_and_status_is_fog_for_now(self):
        cholera = self.by_uri[self.cholera]
        self.assertEqual((cholera["size"], cholera["status"]), (500.2, None))
        self.assertEqual(cholera["burden"], {"dalys": 500.2, "estimated": True, "cause": 302, "method": "direct",
                                             "icd10": "A00.9"})

    def test_a_tie_says_whether_the_owner_has_reviewed_it(self):
        self.assertFalse(self.by_uri[self.brain]["burden"]["reviewed"])
        self.assertNotIn("reviewed", self.by_uri[self.cholera]["burden"])

    def test_a_province_with_no_gbd_cause_has_size_zero_and_no_burden(self):
        quoted = self.by_uri[self.quoted]
        self.assertEqual(quoted["size"], 0)
        self.assertNotIn("burden", quoted)

    def test_carries_the_gbd_causes_on_the_map_and_the_gbd_meta(self):
        self.assertEqual(self.map["meta"]["gbdCauses"], {"302": {"name": "Diarrheal diseases", "dalys": 1000.4,
                                                                 "provinces": 2},
                                                         "417": {"name": "Liver cancer", "dalys": 50.0,
                                                                 "provinces": 1,
                                                                 "members": ["Liver cancer due to hepatitis B"]}})
        self.assertEqual(self.map["meta"]["gbd"], GBD)
        self.assertEqual(self.map["meta"]["crosswalk"], "Project-made cross-walk.")

    def test_every_entity_keeps_icd11_code_title_and_uri(self):
        for node in self.nodes:
            self.assertTrue(node["code"] and node["title"] and node["uri"], node)

    def test_carries_the_icd11_attribution(self):
        self.assertIn("CC BY-ND 3.0 IGO", self.map["meta"]["icd11"]["citation"])
        self.assertEqual(self.map["meta"]["counts"], self.tree["counts"])

    def test_provinces_under_an_approved_cause_inherit_its_status_as_provisional(self):
        approved = {417: {"gbd_cause": "Liver cancer", "gbd_cause_id": 417, "status": 4, "nuance": "Curable if caught early.",
                          "sources": [{"url": "https://example.org/hcc", "title": "HCC"}], "cross_check": "ok",
                          "approved": True}}
        built = site_data.build_map(self.tree, self.crosswalk, self.burden, approved)
        by_uri = {n["uri"]: n for n in list(walk(built["root"]))[1:]}
        self.assertEqual((by_uri[self.brain]["status"], by_uri[self.brain]["provisional"]), (4, True))
        self.assertEqual(by_uri[self.cholera]["status"], None)
        self.assertNotIn("provisional", by_uri[self.cholera])
        self.assertEqual(built["meta"]["gbdCauses"]["417"]["assessment"], {
            "status": 4, "nuance": "Curable if caught early.",
            "sources": [{"url": "https://example.org/hcc", "title": "HCC"}], "crossCheck": "ok"})
        self.assertNotIn("assessment", built["meta"]["gbdCauses"]["302"])

    def test_a_directly_assessed_province_overrides_its_cause_and_is_not_provisional(self):
        cause = {417: {"gbd_cause": "Liver cancer", "status": 4, "nuance": "", "sources": [], "approved": True}}
        own = {self.brain: {"icd11_code": "x", "status": 2, "nuance": "Own note.",
                            "sources": [{"url": "https://example.org/own", "title": "Own"}], "cross_check": "ok"},
               self.quoted: {"icd11_code": "y", "status": 1, "nuance": "", "sources": [], "cross_check": "ok"}}
        built = site_data.build_map(self.tree, self.crosswalk, self.burden, cause, own)
        by_uri = {n["uri"]: n for n in list(walk(built["root"]))[1:]}
        brain, quoted = by_uri[self.brain], by_uri[self.quoted]
        self.assertEqual((brain["status"], brain["provisional"]), (2, False))
        self.assertEqual(brain["assessment"], {"status": 2, "nuance": "Own note.",
                                               "sources": [{"url": "https://example.org/own", "title": "Own"}],
                                               "crossCheck": "ok"})
        # A province with no GBD cause can still be assessed.
        self.assertEqual((quoted["status"], quoted["provisional"], quoted["size"]), (1, False, 0))

    def pipeline_map(self, approved=None, assessed=None):
        bars = {"source": {"dataTimestamp": "2026-10-29T09:00:05", "registeredSince": "2016-10-29", "chembl": "ChEMBL_37"},
                "causes": {"302": {"phase": "phase2", "trials": 7, "url": "https://clinicaltrials.gov/search?cond=x"},
                           "417": {"phase": "phase3", "trials": 40, "url": "https://clinicaltrials.gov/search?cond=y"}}}
        built = site_data.build_map(self.tree, self.crosswalk, self.burden, approved, assessed, bars)
        return built, {n["uri"]: n for n in list(walk(built["root"]))[1:]}

    def test_provinces_inherit_their_causes_pipeline_bar(self):
        built, by_uri = self.pipeline_map()
        self.assertEqual(built["meta"]["gbdCauses"]["302"]["bar"],
                         {"phase": "phase2", "trials": 7, "url": "https://clinicaltrials.gov/search?cond=x"})
        self.assertEqual(built["meta"]["clinicaltrials"], {"dataTimestamp": "2026-10-29T09:00:05",
                                                           "registeredSince": "2016-10-29", "chembl": "ChEMBL_37"})
        self.assertEqual((by_uri[self.cholera]["pipeline"], by_uri[self.brain]["pipeline"]), ("phase2", "phase3"))

    def test_the_chembl_release_reaches_meta(self):
        release = {"release": "ChEMBL_37", "releaseDate": "2026-05-01"}
        built = site_data.build_map(self.tree, self.crosswalk, self.burden, chembl=release)
        self.assertEqual(built["meta"]["chembl"], release)
        self.assertNotIn("chembl", self.map["meta"])

    def test_a_held_province_shows_approved(self):
        cause = {302: {"gbd_cause": "Diarrheal diseases", "status": 2, "nuance": "", "sources": [], "approved": True}}
        own = {self.quoted: {"icd11_code": "y", "status": 1, "nuance": "", "sources": [], "cross_check": "ok"}}
        _, by_uri = self.pipeline_map(cause, own)
        self.assertEqual(by_uri[self.cholera]["pipeline"], "approved")
        # Held with no GBD cause, so no bar to inherit: still Approved.
        self.assertEqual(by_uri[self.quoted]["pipeline"], "approved")

    def test_a_contested_province_keeps_its_causes_phase(self):
        cause = {417: {"gbd_cause": "Liver cancer", "status": 4, "nuance": "", "sources": [], "approved": True}}
        _, by_uri = self.pipeline_map(cause)
        self.assertEqual(by_uri[self.brain]["pipeline"], "phase3")

    def test_a_province_with_no_bar_and_not_held_has_no_pipeline(self):
        _, by_uri = self.pipeline_map()
        self.assertNotIn("pipeline", by_uri[self.quoted])
        self.assertNotIn("pipeline", self.by_uri[self.cholera])
        self.assertNotIn("clinicaltrials", self.map["meta"])

    def test_without_approvals_every_province_is_fog(self):
        self.assertTrue(all(n["status"] is None for n in provinces(self.map["root"])))

    def test_does_not_mutate_the_tree(self):
        self.assertNotIn("size", self.tree["chapters"][1]["children"][0])


if __name__ == "__main__":
    unittest.main()
