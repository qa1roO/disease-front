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


def tsv(*lines):
    return "".join("\t".join(line) + "\r\n" for line in lines)


R = "http://id.who.int/icd/release/11/2026-01/mms/"
MAP_11_TO_10 = tsv(
    ["Linearization (release) URI", "icd11Code", "icd11Chapter", "icd11Title", "icd10Code", "icd10Chapter",
     "icd10Title", "2026-Jan-17"],
    [R + "257068234", "1A00", "01", "Cholera", "A00.9", "I", "Cholera, unspecified"],
    [R + "9", "LD40", "20", "Chromosomal anomalies", "Q90-Q99", "XVII", "Chromosomal abnormalities"],
)
MAP_10_TO_11 = tsv(
    ["10ClassKind", "10DepthInKind", "icd10Code", "icd10Chapter", "icd10Title", "11ClassKind", "11DepthInKind",
     "ICD-11 FoundationURI", "Linearization (releaseURI)", "icd11Code", "icd11Chapter", "icd11Title", "2026-Jan-17"],
    ["chapter", "1", "I", "I", "Infections", "category", "1", "x", "y", "1H0Z", "01", "Infection"],
    ["block", "1", "A00-A09", "I", "Intestinal", "category", "1", "x", "y", "1A40", "01", "Gastroenteritis"],
    ["category", "1", "A00", "I", "Cholera", "category", "1", "x", "y", "1A00", "01", "Cholera"],
    ["category", "2", "A00.9", "I", "Cholera, unspecified", "category", "1", "x", "y", "1A00", "01", "Cholera"],
    ["modifiedcategory", "3", "B18.00", "I", "Hepatitis B", "category", "1", "x", "y", "1E50", "01", "Hepatitis B"],
)


class MappingTablesTest(unittest.TestCase):
    def test_icd11_to_icd10_is_keyed_by_the_tree_uri(self):
        self.assertEqual(icd11.parse_11_to_10(MAP_11_TO_10), {
            "http://id.who.int/icd/release/11/mms/257068234": "A00.9",
            "http://id.who.int/icd/release/11/mms/9": "Q90-Q99",
        })

    def test_icd10_codes_are_the_categories_with_their_chapter(self):
        self.assertEqual(icd11.parse_icd10_codes(MAP_10_TO_11), [("A00", "I"), ("A00.9", "I"), ("B18.00", "I")])


if __name__ == "__main__":
    unittest.main()
