import unittest

from pipeline import icd11, site_data, tree
from tests.pipeline.fixtures import TABULATION
from tests.pipeline.test_tree import walk


class BuildMapTest(unittest.TestCase):
    def setUp(self):
        self.tree = tree.build_tree(icd11.parse_tabulation(TABULATION), version="test")
        self.map = site_data.build_map(self.tree)
        self.nodes = list(walk(self.map["root"]))[1:]

    def test_root_holds_the_chapters(self):
        self.assertEqual([c["code"] for c in self.map["root"]["children"]], ["01", "02"])

    def test_every_province_is_equal_sized_fog_for_now(self):
        provinces = [n for n in self.nodes if "children" not in n]
        self.assertEqual(len(provinces), self.tree["counts"]["provinces"])
        for p in provinces:
            self.assertEqual((p["size"], p["status"]), (1, None))

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
