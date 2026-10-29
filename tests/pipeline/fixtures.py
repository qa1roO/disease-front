"""A tiny ICD-11 simple tabulation in the real file's format, for tests."""

HEADER = ("Foundation URI\tLinearization URI\tCode\tBlockId\tTitle\tClassKind\tDepthInKind\tIsResidual\t"
          "ChapterNo\tBrowserLink\tisLeaf\tPrimary tabulation\tGrouping1\tGrouping2\tGrouping3\tGrouping4\t"
          "Grouping5\tCodingNote\tParent\tVersion:2026 Jan 17 - 05:30 UTC")

E = "http://id.who.int/icd/entity/"
M = "http://id.who.int/icd/release/11/mms/"


def row(fid, code, block, title, kind, residual, chapter, leaf, parent, note="", suffix=""):
    foundation = "" if residual else E + fid
    linear = M + fid + suffix
    fields = [foundation, linear, code, block, f'"{title}"', kind, "1", str(residual), chapter,
              '"=hyperlink(""https://icd.who.int/browse/latestrelease/mms/en#x"",""browser"")"',
              str(leaf), "True", "", "", "", "", "", note, E + parent if parent else ""]
    return "\t".join(fields)


ROWS = [
    row("1", "", "", "Certain infectious or parasitic diseases", "chapter", False, "01", False, ""),
    row("10", "", "BlockL1-1A0", "- Gastroenteritis or colitis of infectious origin", "block", False, "01", False, "1"),
    row("100", "1A00", "", "- - Cholera", "category", False, "01", True, "10"),
    row("101", "1A03", "", "- - Intestinal infections due to Escherichia coli", "category", False, "01", False, "10"),
    row("1010", "1A03.0", "", "- - - Enteropathogenic Escherichia coli infection", "category", False, "01", True,
        "101", note='"Line one\nline two"'),
    row("101", "1A03.Y", "", "- - - Other specified Escherichia coli", "category", True, "01", True, "101",
        suffix="/other"),
    row("101", "1A03.Z", "", "- - - Escherichia coli, unspecified", "category", True, "01", True, "101",
        suffix="/unspecified"),
    row("102", "1A04", "", '- - So-called ""quoted"" infection', "category", False, "01", True, "10"),
    row("2", "", "", "Neoplasms", "chapter", False, "02", False, ""),
    row("20", "2A00", "", "- Brain neoplasm", "category", False, "02", True, "2"),
    row("21", "", "BlockL1-2B0", "- Empty block of residuals", "block", False, "02", False, "2"),
    row("21", "2B0Z", "", "- - Neoplasms, unspecified", "category", True, "02", True, "21", suffix="/unspecified"),
    row("3", "", "", "Symptoms, signs or clinical findings, not elsewhere classified", "chapter", False, "21", False, ""),
    row("30", "MA00", "", "- Fever", "category", False, "21", True, "3"),
    row("4", "", "", "Extension Codes", "chapter", False, "X", False, ""),
    row("40", "XA00", "", "- Some extension", "category", False, "X", True, "4"),
]

TABULATION = "﻿" + HEADER + "\r\n" + "\r\n".join(ROWS) + "\r\n"
