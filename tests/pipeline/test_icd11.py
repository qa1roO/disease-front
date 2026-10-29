import unittest

from pipeline import icd11
from tests.pipeline.fixtures import ROWS, TABULATION


class ParseTabulationTest(unittest.TestCase):
    def setUp(self):
        self.rows = icd11.parse_tabulation(TABULATION)

    def test_one_row_per_record_even_when_a_coding_note_has_a_line_break(self):
        self.assertEqual(len(self.rows), len(ROWS))
        note = next(r for r in self.rows if r["Code"] == "1A03.0")["CodingNote"]
        self.assertIn("line two", note)

    def test_titles_lose_quotes_and_depth_dashes(self):
        titles = {r["Code"]: r["Title"] for r in self.rows}
        self.assertEqual(titles["1A00"], "Cholera")
        self.assertEqual(titles["1A03.0"], "Enteropathogenic Escherichia coli infection")
        self.assertEqual(titles["1A04"], 'So-called "quoted" infection')

    def test_residual_rows_keep_their_linearization_uri(self):
        residual = next(r for r in self.rows if r["Code"] == "1A03.Z")
        self.assertEqual(residual["Foundation URI"], "")
        self.assertTrue(residual["Linearization URI"].endswith("/101/unspecified"))

    def test_reads_the_version_from_the_header(self):
        self.assertEqual(icd11.tabulation_version(TABULATION), "2026 Jan 17 - 05:30 UTC")


if __name__ == "__main__":
    unittest.main()
