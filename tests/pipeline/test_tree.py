import unittest

from pipeline import icd11, tree
from tests.pipeline.fixtures import TABULATION


def walk(node):
    yield node
    for child in node.get("children", []):
        yield from walk(child)


class BuildTreeTest(unittest.TestCase):
    def setUp(self):
        self.tree = tree.build_tree(icd11.parse_tabulation(TABULATION), version="test")
        self.nodes = [n for chapter in self.tree["chapters"] for n in walk(chapter)]

    def test_keeps_only_disease_chapters_in_icd_order(self):
        self.assertEqual([c["code"] for c in self.tree["chapters"]], ["01", "02"])

    def test_drops_residual_entries(self):
        codes = {n["code"] for n in self.nodes}
        self.assertNotIn("1A03.Y", codes)
        self.assertNotIn("1A03.Z", codes)

    def test_drops_territories_left_empty(self):
        self.assertNotIn("BlockL1-2B0", {n["code"] for n in self.nodes})

    def test_territories_nest_to_any_depth(self):
        block = self.tree["chapters"][0]["children"][0]
        self.assertEqual(block["kind"], "block")
        self.assertEqual([c["code"] for c in block["children"]], ["1A00", "1A03", "1A04"])
        e_coli = block["children"][1]
        self.assertEqual([c["code"] for c in e_coli["children"]], ["1A03.0"])

    def test_provinces_are_leaf_categories_and_have_no_children_key(self):
        provinces = [n for n in self.nodes if "children" not in n]
        self.assertEqual(sorted(n["code"] for n in provinces), ["1A00", "1A03.0", "1A04", "2A00"])
        self.assertTrue(all(n["kind"] == "category" for n in provinces))

    def test_every_entity_keeps_icd11_code_title_and_uri(self):
        for node in self.nodes:
            self.assertTrue(node["code"] and node["title"], node)
            self.assertTrue(node["uri"].startswith("http://id.who.int/icd/release/11/mms/"), node)

    def test_counts(self):
        self.assertEqual(self.tree["counts"], {"chapters": 2, "territories": 2, "provinces": 4})

    def test_records_the_source(self):
        self.assertEqual(self.tree["icd11"]["version"], "test")
        self.assertIn("CC BY-ND 3.0 IGO", self.tree["icd11"]["citation"])


if __name__ == "__main__":
    unittest.main()
