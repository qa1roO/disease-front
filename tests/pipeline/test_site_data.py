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

    def test_does_not_mutate_the_tree(self):
        self.assertNotIn("size", self.tree["chapters"][1]["children"][0])


if __name__ == "__main__":
    unittest.main()
