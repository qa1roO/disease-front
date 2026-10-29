import tempfile
import unittest
from pathlib import Path

from pipeline import mesh

BURDEN = {"causes": {
    "493": {"name": "Ischemic heart disease", "dalys": 1.9e8, "provinces": 12},
    "554": {"name": "Motor neuron disease", "dalys": 1.2e6, "provinces": 3},
    "418": {"name": "Liver cancer due to hepatitis B", "dalys": 6e6, "provinces": 0},
}}
IDS = {"Coronary Artery Disease": "D003324", "Myocardial Ischemia": "D017202",
       "Amyotrophic Lateral Sclerosis": "D000690", "Motor Neuron Disease": "D016472",
       "Liver Neoplasms": "D008113", "Hepatitis B": "D006509"}
DRAFTS = {493: ["Coronary Artery Disease", "Myocardial Ischemia"],
          554: ["Amyotrophic Lateral Sclerosis", "Motor Neuron Disease"],
          418: ["Liver Neoplasms", "Hepatitis B"]}


def build(drafts=DRAFTS, existing=None):
    return mesh.build(mesh.causes(BURDEN), drafts, existing or {}, IDS.get)


class CausesTest(unittest.TestCase):
    def test_every_gbd_cause_biggest_burden_first_even_without_provinces(self):
        self.assertEqual([c["id"] for c in mesh.causes(BURDEN)], [493, 418, 554])


class BuildTest(unittest.TestCase):
    def test_every_cause_gets_its_resolved_terms_unreviewed(self):
        entries, problems = build()
        self.assertEqual(problems, {})
        self.assertEqual(list(entries), [493, 418, 554])
        self.assertEqual(entries[493], {"cause": "Ischemic heart disease",
                                        "terms": {"D003324": "Coronary Artery Disease",
                                                  "D017202": "Myocardial Ischemia"},
                                        "reviewed": False})

    def test_a_reviewed_entry_is_kept_whatever_the_draft_says(self):
        mine = {"cause": "Motor neuron disease", "terms": {"D000690": "Amyotrophic Lateral Sclerosis"},
                "reviewed": True}
        entries, _ = build(existing={554: mine})
        self.assertEqual(entries[554], mine)

    def test_an_unreviewed_entry_follows_the_current_draft(self):
        old = {"cause": "Motor neuron disease", "terms": {"D016472": "Motor Neuron Disease"}, "reviewed": False}
        entries, _ = build(existing={554: old})
        self.assertEqual(list(entries[554]["terms"]), ["D000690", "D016472"])

    def test_an_unknown_heading_rejects_the_draft_and_keeps_the_old_entry(self):
        old = {"cause": "Motor neuron disease", "terms": {"D016472": "Motor Neuron Disease"}, "reviewed": False}
        entries, problems = build(drafts={**DRAFTS, 554: ["Lou Gehrig Disease"]}, existing={554: old})
        self.assertEqual(problems, {554: ["MeSH heading not found: Lou Gehrig Disease"]})
        self.assertEqual(entries[554], old)

    def test_a_cause_with_no_draft_and_no_entry_is_reported_and_left_out(self):
        entries, problems = build(drafts={493: DRAFTS[493]})
        self.assertEqual(problems, {418: ["no draft"], 554: ["no draft"]})
        self.assertEqual(list(entries), [493])

    def test_an_empty_draft_is_a_problem(self):
        _, problems = build(drafts={**DRAFTS, 418: []})
        self.assertEqual(problems, {418: ["needs at least one MeSH heading"]})


class FirstFoundTest(unittest.TestCase):
    def test_falls_back_to_the_next_lookup_for_a_label_the_current_mesh_renamed(self):
        current = {"Major Depressive Disorder": "D003865"}.get
        previous = {"Depressive Disorder, Major": "D003865"}.get
        resolve = mesh.first_found(current, previous)
        self.assertEqual(resolve("Depressive Disorder, Major"), "D003865")
        self.assertEqual(resolve("Major Depressive Disorder"), "D003865")
        self.assertIsNone(resolve("Lou Gehrig Disease"))


class FileTest(unittest.TestCase):
    def test_write_then_read_round_trips_with_a_header(self):
        entries, _ = build()
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "mesh.yaml"
            mesh.write(path, entries)
            self.assertTrue(path.read_text(encoding="utf-8").startswith("# Stage 5"))
            self.assertEqual(mesh.read(path), entries)

    def test_reading_a_missing_file_gives_nothing(self):
        self.assertEqual(mesh.read(Path("no/such/mesh.yaml")), {})

    def test_reviewed_terms_are_the_only_ones_stage_7_sees(self):
        entries, _ = build()
        entries[554] = {**entries[554], "reviewed": True}
        self.assertEqual(mesh.reviewed_terms(entries), {554: {"D000690": "Amyotrophic Lateral Sclerosis",
                                                              "D016472": "Motor Neuron Disease"}})

    def test_drafts_are_read_from_every_yaml_file_keyed_by_cause_id(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "a.yaml").write_text("493: [Coronary Artery Disease]\n", encoding="utf-8")
            Path(d, "b.yaml").write_text("'554':\n- Motor Neuron Disease\n", encoding="utf-8")
            self.assertEqual(mesh.read_drafts(Path(d)), {493: ["Coronary Artery Disease"],
                                                         554: ["Motor Neuron Disease"]})


if __name__ == "__main__":
    unittest.main()
