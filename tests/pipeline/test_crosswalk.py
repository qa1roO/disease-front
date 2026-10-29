import unittest

from pipeline import crosswalk as cw

# A tiny ICD-10: chapter IV (E00-E90) and XVII (Q00-Q99), as (code, chapter) pairs.
ICD10 = [(c, "IV") for c in ("E10", "E10.0", "E10.2", "E10.9", "E11", "E11.2", "E11.9", "E66")] + \
        [(c, "XVII") for c in ("Q90", "Q90.0", "Q90.9", "Q91", "Q91.0", "Q92", "Q99")]

# GBD causes: (cause_id, name, sort_order, eligible)
CAUSES = {
    975: {"name": "Diabetes mellitus type 1", "sort": 1},
    976: {"name": "Diabetes mellitus type 2", "sort": 2},
    997: {"name": "CKD due to diabetes type 1", "sort": 3},
    645: {"name": "Down syndrome", "sort": 4},
    648: {"name": "Other chromosomal abnormalities", "sort": 5},
}

ICD_ROWS = [
    {"cause_id": "975", "variant": "cod", "icd10": "E10-E10.1, E10.3-E10.9"},
    {"cause_id": "976", "variant": "cod", "icd10": "E11-E11.1, E11.3-E11.9"},
    {"cause_id": "997", "variant": "cod", "icd10": "E10.2"},
    {"cause_id": "976", "variant": "nonfatal", "icd10": "E11-E119"},
    {"cause_id": "645", "variant": "cod", "icd10": "Q90-Q90.9"},
    {"cause_id": "645", "variant": "nonfatal", "icd10": "Q90-Q909"},
    {"cause_id": "648", "variant": "cod", "icd10": "Q91-Q92.9"},
    {"cause_id": "999", "variant": "cod", "icd10": "E66"},  # not an eligible cause
]


def index(rows=ICD_ROWS):
    return cw.CauseIndex(rows, cw.lookup_steps(set(CAUSES), {}))


class CodeTest(unittest.TestCase):
    def test_keys_drop_dots_and_compare_both_notations(self):
        self.assertEqual(cw.code_key("E10.9"), "E109")
        self.assertEqual(cw.code_key("e109 "), "E109")

    def test_ranges_include_their_subcodes(self):
        ranges = cw.parse_code_list("A68-A70, B63, I20-I25.9")
        self.assertTrue(cw.in_ranges("A700", ranges))  # under the upper bound's code
        self.assertTrue(cw.in_ranges("B631", ranges))  # under a single code
        self.assertTrue(cw.in_ranges("I259", ranges))
        self.assertFalse(cw.in_ranges("I26", ranges))
        self.assertFalse(cw.in_ranges("A67", ranges))

    def test_a_category_is_not_inside_a_range_that_starts_below_it(self):
        self.assertFalse(cw.in_ranges("E10", cw.parse_code_list("E10.3-E11.1")))


class ExpandTest(unittest.TestCase):
    def setUp(self):
        self.universe = cw.Icd10(ICD10)

    def test_a_leaf_code_is_itself(self):
        self.assertEqual(self.universe.expand("E10.9"), ["E109"])

    def test_a_category_expands_to_its_leaves(self):
        self.assertEqual(self.universe.expand("E10"), ["E100", "E102", "E109"])

    def test_a_block_expands_to_the_leaves_of_its_categories(self):
        self.assertEqual(self.universe.expand("Q90-Q91"), ["Q900", "Q909", "Q910"])

    def test_a_chapter_expands_to_all_its_leaves(self):
        self.assertEqual(len(self.universe.expand("XVII")), 5)

    def test_an_unknown_code_is_kept_as_is(self):
        self.assertEqual(self.universe.expand("Z99.9"), ["Z999"])

    def test_no_mapping_expands_to_nothing(self):
        self.assertEqual(self.universe.expand("No Mapping"), [])
        self.assertEqual(self.universe.expand(""), [])


class CauseIndexTest(unittest.TestCase):
    def test_cause_of_death_list_wins_over_nonfatal(self):
        rows = ICD_ROWS + [{"cause_id": "997", "variant": "nonfatal", "icd10": "E10-E109"}]
        self.assertEqual(index(rows).causes_for("E109"), {975})

    def test_falls_back_to_nonfatal_when_no_cod_cause_has_the_code(self):
        self.assertEqual(index().causes_for("E112"), {976})  # cod leaves E11.2 out, nonfatal has it

    def test_ignores_causes_that_are_not_eligible(self):
        self.assertEqual(index().causes_for("E66"), set())

    def test_project_codes_come_after_cause_of_death_lists_before_nonfatal_and_groups_last(self):
        rows = ICD_ROWS + [
            {"cause_id": "976", "variant": "project", "icd10": "E10.9, E66"},
            {"cause_id": "997", "variant": "nonfatal", "icd10": "E66"},
            {"cause_id": "587", "variant": "cod", "icd10": "E10-E14.9"},  # a GBD parent, here a group
        ]
        steps = cw.lookup_steps(set(CAUSES), {587: {"level": 3}})
        self.assertEqual([v for v, _ in steps], ["cod", "project", "nonfatal", "cod", "nonfatal"])
        idx = cw.CauseIndex(rows, steps)
        self.assertEqual(idx.causes_for("E109"), {975})  # GBD's cause-of-death list wins
        self.assertEqual(idx.causes_for("E66"), {976})   # then the project's, over a nonfatal list
        self.assertEqual(idx.causes_for("E119"), {976})  # nonfatal still counts where nothing else has the code
        self.assertEqual(idx.causes_for("E14"), {587})   # then the parent group


class AssignTest(unittest.TestCase):
    def setUp(self):
        self.universe, self.index = cw.Icd10(ICD10), index()

    def assign(self, target):
        return cw.assign(target, self.universe, self.index, CAUSES)

    def test_a_single_code_maps_directly(self):
        self.assertEqual(self.assign("E10.9"), {"cause": 975, "method": "direct", "votes": {975: 1}})

    def test_majority_over_the_codes_in_a_range(self):
        result = self.assign("Q90-Q92")  # Q90.0, Q90.9 -> Down; Q91.0, Q92 -> other chromosomal
        self.assertEqual(result["method"], "tie")
        self.assertEqual(result["candidates"], [645, 648])
        result = self.assign("Q90")
        self.assertEqual((result["cause"], result["method"]), (645, "direct"))
        result = self.assign("E10")  # E10.0, E10.9 -> type 1; E10.2 -> CKD
        self.assertEqual((result["cause"], result["method"]), (975, "majority"))
        self.assertEqual(result["votes"], {975: 2, 997: 1})

    def test_tied_candidates_come_in_gbd_order(self):
        self.assertEqual(self.assign("XVII")["candidates"], [645, 648])

    def test_no_cause_means_unmapped(self):
        self.assertEqual(self.assign("E66"), {"cause": None, "method": "none", "votes": {}})
        self.assertEqual(self.assign("No Mapping")["method"], "none")


PROVINCES = [
    {"uri": "u1", "code": "5A10", "title": "Type 1 diabetes mellitus"},
    {"uri": "u2", "code": "5A11", "title": "Type 2 diabetes mellitus"},
    {"uri": "u3", "code": "5A12", "title": "Another type 2"},
    {"uri": "u4", "code": "LD40", "title": "Chromosomal anomalies"},
    {"uri": "u5", "code": "5B81", "title": "Obesity"},
]
WHO = {"u1": "E10.9", "u2": "E11.9", "u3": "E11", "u4": "Q90-Q92", "u5": "E66"}
DALYS = {975: 300.0, 976: 1000.0, 997: 50.0, 645: 80.0, 648: 20.0}


class BuildTest(unittest.TestCase):
    def build(self, review=None):
        return cw.build(PROVINCES, WHO, cw.Icd10(ICD10), index(), CAUSES, DALYS, review or [])

    def test_ties_go_to_review_with_the_first_candidate_as_placeholder(self):
        result = self.build()
        (tie,) = result["review"]
        self.assertEqual((tie["uri"], tie["resolution"], tie["reviewed"]), ("u4", 645, False))
        self.assertEqual([c["cause_id"] for c in tie["candidates"]], [645, 648])
        self.assertEqual(result["crosswalk"]["u4"]["cause"], 645)
        self.assertEqual(result["crosswalk"]["u4"]["method"], "review")
        self.assertFalse(result["crosswalk"]["u4"]["reviewed"])

    def test_an_edited_resolution_is_kept_and_applied(self):
        edited = [{"uri": "u4", "resolution": 648, "reviewed": True, "note": "why"}]
        result = self.build(edited)
        self.assertEqual(result["crosswalk"]["u4"]["cause"], 648)
        self.assertEqual((result["review"][0]["resolution"], result["review"][0]["reviewed"]), (648, True))
        self.assertEqual(result["review"][0]["note"], "why")

    def test_a_null_resolution_leaves_the_province_in_fog(self):
        result = self.build([{"uri": "u4", "resolution": None, "reviewed": True}])
        self.assertIsNone(result["crosswalk"]["u4"]["cause"])
        self.assertNotIn("u4", result["burden"])

    def test_each_cause_is_split_equally_among_its_provinces(self):
        burden = self.build()["burden"]
        self.assertEqual(burden["u1"], {"dalys": 300.0, "cause": 975, "estimated": False})
        self.assertEqual(burden["u2"], {"dalys": 500.0, "cause": 976, "estimated": True})
        self.assertEqual(burden["u3"]["dalys"], 500.0)

    def test_unmapped_provinces_get_no_burden(self):
        result = self.build()
        self.assertEqual(result["crosswalk"]["u5"]["method"], "none")
        self.assertNotIn("u5", result["burden"])

    def test_sizes_add_up_to_the_covered_causes(self):
        result = self.build()
        covered = sum(DALYS[c] for c, s in result["causes"].items() if s["provinces"])
        self.assertAlmostEqual(sum(p["dalys"] for p in result["burden"].values()), covered)

    def test_a_group_counts_its_members_dalys_once(self):
        causes = {**CAUSES, 587: {"name": "Diabetes mellitus", "sort": 0, "members": [975, 976]}}
        rows = [{"cause_id": "587", "variant": "cod", "icd10": "E10-E11.9"}]
        result = cw.build(PROVINCES[:2], WHO, cw.Icd10(ICD10), cw.CauseIndex(rows, [("cod", {587})]), causes,
                          {**DALYS, 587: 1300.0}, [])
        self.assertEqual(result["burden"]["u1"], {"dalys": 650.0, "cause": 587, "estimated": True})
        self.assertEqual(result["stats"]["dalys_total"], 1450.0)
        self.assertEqual(result["stats"]["dalys_covered"], 1300.0)
        self.assertEqual(result["causes"][587]["members"], [975, 976])

    def test_report_counts(self):
        stats = self.build()["stats"]
        self.assertEqual(stats["provinces"], 5)
        self.assertEqual(stats["mapped"], 4)
        self.assertEqual(stats["unmapped"], 1)
        self.assertEqual(stats["ties"], 1)
        self.assertAlmostEqual(stats["dalys_covered_share"], (300 + 1000 + 80) / 1450)


if __name__ == "__main__":
    unittest.main()
