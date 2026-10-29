import tempfile
import unittest
from pathlib import Path

import yaml

from pipeline import proposals

BURDEN = {"causes": {
    "493": {"name": "Ischemic heart disease", "dalys": 1.9e8, "provinces": 12, "group": "Non-communicable diseases"},
    "554": {"name": "Motor neuron disease", "dalys": 1.2e6, "provinces": 3, "group": "Non-communicable diseases"},
    "417": {"name": "Liver cancer", "dalys": 1.3e7, "provinces": 2, "members": [418],
            "group": "Non-communicable diseases"},
    "418": {"name": "Liver cancer due to hepatitis B", "dalys": 6e6, "provinces": 0,
            "group": "Non-communicable diseases"},
    "298": {"name": "HIV/AIDS", "dalys": 9.9e5, "provinces": 4,
            "group": "Communicable, maternal, neonatal, and nutritional diseases"},
}}

GOOD = {"status": 3, "nuance": "Most patients live near-normal lives on statins, antiplatelets and revascularisation.",
        "sources": [{"url": "https://example.org/ihd", "title": "IHD review"}], "mesh": ["D003324"]}


class CausesTest(unittest.TestCase):
    def test_non_communicable_causes_on_the_map_biggest_first(self):
        self.assertEqual([c["id"] for c in proposals.ncd_causes(BURDEN)], [493, 417, 554])

    def test_a_group_lists_its_members_for_the_proposer(self):
        liver = next(c for c in proposals.ncd_causes(BURDEN) if c["id"] == 417)
        self.assertEqual(liver["members"], ["Liver cancer due to hepatitis B"])

    def test_file_name_is_id_and_slug(self):
        self.assertEqual(proposals.file_name({"id": 493, "name": "Ischemic heart disease"}),
                         "493-ischemic-heart-disease.yaml")
        self.assertEqual(proposals.file_name({"id": 1, "name": "Alzheimer's disease & other dementias"}),
                         "1-alzheimer-s-disease-other-dementias.yaml")


class CrossCheckTest(unittest.TestCase):
    approved = {"D003324": ["CHEMBL25"], "D000690": ["CHEMBL1201"]}

    def check(self, status, mesh):
        return proposals.cross_check({"status": status, "mesh": mesh}, self.approved)

    def test_held_with_an_approved_drug_is_ok(self):
        self.assertEqual(self.check(3, ["D003324"]), "ok")

    def test_curable_or_controlled_without_an_approved_drug_is_flagged(self):
        self.assertTrue(self.check(2, ["D999999"]).startswith("flag: claims Curable but ChEMBL has no approved drug"))
        self.assertTrue(self.check(3, []).startswith("flag: claims Controlled"))

    def test_untreatable_with_an_approved_drug_is_flagged_naming_the_count(self):
        self.assertEqual(self.check(5, ["D000690"]),
                         "flag: claims Untreatable but ChEMBL has 1 approved drug for D000690")

    def test_eradicated_and_treatable_need_no_drug_either_way(self):
        self.assertEqual(self.check(1, []), "ok")
        self.assertEqual(self.check(4, []), "ok")
        self.assertEqual(self.check(4, ["D000690"]), "ok")

    def test_approved_drugs_index_keeps_phase_4_indications_by_mesh_id(self):
        rows = [{"mesh_id": "D1", "max_phase_for_ind": "4.0", "parent_molecule_chembl_id": "CHEMBL1"},
                {"mesh_id": "D1", "max_phase_for_ind": "4.0", "parent_molecule_chembl_id": "CHEMBL1"},
                {"mesh_id": "D1", "max_phase_for_ind": 4, "parent_molecule_chembl_id": "CHEMBL2"},
                {"mesh_id": "D2", "max_phase_for_ind": "3.0", "parent_molecule_chembl_id": "CHEMBL3"},
                {"mesh_id": None, "max_phase_for_ind": "4.0", "parent_molecule_chembl_id": "CHEMBL4"}]
        self.assertEqual(proposals.approved_drugs(rows), {"D1": ["CHEMBL1", "CHEMBL2"]})


class ValidateTest(unittest.TestCase):
    def test_a_good_proposal_has_no_problems(self):
        self.assertEqual(proposals.problems(GOOD, lambda url: True), [])

    def test_status_must_be_1_to_5_and_sources_must_exist_and_resolve(self):
        bad = {"status": 7, "sources": [{"url": "https://dead.example", "title": "x"}, {"title": "no url"}]}
        self.assertEqual(proposals.problems(bad, lambda url: url != "https://dead.example"), [
            "status must be an integer 1-5, got 7",
            "source does not resolve: https://dead.example",
            "source has no url: {'title': 'no url'}",
        ])
        self.assertEqual(proposals.problems({"status": 4, "sources": []}, lambda url: True),
                         ["needs at least one source"])


class ResolvesTest(unittest.TestCase):
    def test_ok_only_on_http_200_after_redirects(self):
        calls = []

        def opener(url, method):
            calls.append((url, method))
            return {"https://a": 200, "https://b": 404}.get(url, 405 if method == "HEAD" else 200)

        self.assertTrue(proposals.resolves("https://a", opener))
        self.assertFalse(proposals.resolves("https://b", opener))
        # A server that refuses HEAD gets a GET.
        self.assertTrue(proposals.resolves("https://c", opener))
        self.assertIn(("https://c", "GET"), calls)

    def test_network_errors_mean_it_does_not_resolve(self):
        def opener(url, method):
            raise OSError("no route")

        self.assertFalse(proposals.resolves("https://x", opener, pause=0))

    def test_a_dropped_request_gets_a_second_try(self):
        answers = iter([OSError("reset"), 200])

        def opener(url, method):
            answer = next(answers)
            if isinstance(answer, Exception):
                raise answer
            return answer

        self.assertTrue(proposals.resolves("https://x", opener, pause=0))

    def test_only_http_urls(self):
        self.assertFalse(proposals.resolves("ftp://x", lambda u, m: 200))


class RunTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.asked = []

    def proposer(self, answers):
        answers = iter(answers)

        def propose(cause, feedback):
            self.asked.append((cause["id"], feedback))
            return dict(next(answers))
        return propose

    def run_stage(self, causes, propose, refresh=False):
        return proposals.run(causes, self.tmp, propose, lambda url: url != "https://dead.example",
                             {"D003324": ["CHEMBL25"]}, refresh=refresh, log=lambda line: None)

    def read(self, cause):
        return yaml.safe_load((self.tmp / proposals.file_name(cause)).read_text(encoding="utf-8"))

    IHD = {"id": 493, "name": "Ischemic heart disease", "dalys": 1.9e8, "members": []}

    def test_writes_the_spec_format_unapproved(self):
        self.run_stage([self.IHD], self.proposer([GOOD]))
        p = self.read(self.IHD)
        self.assertEqual(list(p), ["gbd_cause", "gbd_cause_id", "status", "nuance", "sources", "mesh",
                                   "cross_check", "approved", "fingerprint"])
        self.assertEqual((p["gbd_cause"], p["status"], p["cross_check"], p["approved"]),
                         ("Ischemic heart disease", 3, "ok", False))

    def test_a_dead_source_is_rejected_and_retried_with_the_reason(self):
        dead = {**GOOD, "sources": [{"url": "https://dead.example", "title": "gone"}]}
        result = self.run_stage([self.IHD], self.proposer([dead, GOOD]))
        self.assertEqual([f for _, f in self.asked], [[], ["source does not resolve: https://dead.example"]])
        self.assertEqual(self.read(self.IHD)["sources"], GOOD["sources"])
        self.assertEqual(result["written"], [493])

    def test_gives_up_after_three_tries_and_writes_nothing(self):
        dead = {**GOOD, "sources": [{"url": "https://dead.example", "title": "gone"}]}
        result = self.run_stage([self.IHD], self.proposer([dead] * 3))
        self.assertEqual(len(self.asked), 3)
        self.assertFalse((self.tmp / proposals.file_name(self.IHD)).exists())
        self.assertEqual(result["failed"], {493: ["source does not resolve: https://dead.example"]})

    def test_rerun_skips_existing_files_without_calling_the_proposer(self):
        self.run_stage([self.IHD], self.proposer([GOOD]))
        result = self.run_stage([self.IHD], self.proposer([]))
        self.assertEqual(result["kept"], [493])
        self.assertEqual(len(self.asked), 1)

    def test_refresh_regenerates_only_untouched_unapproved_files(self):
        other = {"id": 554, "name": "Motor neuron disease", "dalys": 1.2e6, "members": []}
        third = {"id": 417, "name": "Liver cancer", "dalys": 1.3e7, "members": []}
        self.run_stage([self.IHD, other, third], self.proposer([GOOD, GOOD, GOOD]))
        path = self.tmp / proposals.file_name(self.IHD)
        path.write_text(path.read_text(encoding="utf-8").replace("approved: false", "approved: true"), encoding="utf-8")
        edited = self.tmp / proposals.file_name(other)
        edited.write_text(edited.read_text(encoding="utf-8").replace("status: 3", "status: 4"), encoding="utf-8")

        result = self.run_stage([self.IHD, other, third], self.proposer([{**GOOD, "status": 2}]), refresh=True)
        self.assertEqual(sorted(result["kept"]), [493, 554])
        self.assertEqual(result["written"], [417])
        self.assertTrue(self.read(self.IHD)["approved"])
        self.assertEqual(self.read(other)["status"], 4)
        self.assertEqual(self.read(third)["status"], 2)

    def test_flags_are_counted_and_listed_in_the_index(self):
        result = self.run_stage([self.IHD], self.proposer([{**GOOD, "mesh": []}]))
        self.assertEqual(list(result["flagged"]), [493])
        index = (self.tmp / "INDEX.md").read_text(encoding="utf-8")
        self.assertIn("FLAG", index)
        self.assertIn("493-ischemic-heart-disease.yaml", index)


class SessionDraftsTest(unittest.TestCase):
    """Stage 6 runs from a Claude session: drafts in a YAML file, MeSH headings resolved to descriptor IDs."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "batch-1.yaml").write_text(yaml.safe_dump({493: {
            "status": 3, "nuance": "n", "sources": GOOD["sources"],
            "mesh": ["Coronary Artery Disease", "Not A Heading"]}}), encoding="utf-8")
        self.lookup = {"Coronary Artery Disease": "D003324"}.get

    def test_reads_every_draft_file_keyed_by_cause_id(self):
        self.assertEqual(list(proposals.read_drafts(self.tmp)), [493])

    def test_proposer_resolves_mesh_headings_and_reports_unknown_ones(self):
        propose = proposals.draft_proposer(proposals.read_drafts(self.tmp), self.lookup)
        draft = propose({"id": 493}, [])
        self.assertEqual(draft["mesh"], {"D003324": "Coronary Artery Disease"})
        self.assertEqual(proposals.problems(draft, lambda url: True), ["MeSH heading not found: Not A Heading"])

    def test_a_cause_without_a_draft_fails_with_no_draft(self):
        propose = proposals.draft_proposer({}, self.lookup)
        out = Path(tempfile.mkdtemp())
        result = proposals.run([{"id": 554, "name": "Motor neuron disease", "dalys": 1, "members": []}], out, propose,
                               lambda url: True, {}, tries=1, log=lambda line: None)
        self.assertEqual(result["failed"], {554: ["no draft"]})

    def test_mesh_as_id_to_heading_mapping_feeds_the_cross_check(self):
        self.assertEqual(proposals.cross_check({"status": 3, "mesh": {"D003324": "Coronary Artery Disease"}},
                                               {"D003324": ["CHEMBL25"]}), "ok")


class ApprovedTest(unittest.TestCase):
    def test_reads_only_approved_proposals_keyed_by_cause_id(self):
        tmp = Path(tempfile.mkdtemp())
        for cid, approved in ((1, True), (2, False)):
            (tmp / f"{cid}-x.yaml").write_text(yaml.safe_dump(
                {"gbd_cause": "x", "gbd_cause_id": cid, "status": 4, "nuance": "n", "sources": GOOD["sources"],
                 "cross_check": "ok", "approved": approved}), encoding="utf-8")
        (tmp / "INDEX.md").write_text("# not yaml", encoding="utf-8")
        self.assertEqual(list(proposals.load_approved(tmp)), [1])
        self.assertEqual(proposals.load_approved(tmp)[1]["status"], 4)


class EventsTest(unittest.TestCase):
    def test_each_approval_that_changes_a_status_appends_one_event(self):
        events = [{"date": "2026-10-01", "cause": 493, "name": "Ischemic heart disease", "from": None, "to": 4}]
        approved = {493: {"gbd_cause": "Ischemic heart disease", "status": 3},
                    554: {"gbd_cause": "Motor neuron disease", "status": 5}}
        new = proposals.record_events(approved, events, "2026-10-29")
        self.assertEqual(new[1:], [
            {"date": "2026-10-29", "cause": 493, "name": "Ischemic heart disease", "from": 4, "to": 3},
            {"date": "2026-10-29", "cause": 554, "name": "Motor neuron disease", "from": None, "to": 5},
        ])
        self.assertEqual(proposals.record_events(approved, new, "2026-10-30"), new)


if __name__ == "__main__":
    unittest.main()
