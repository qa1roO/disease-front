"""Reading the WHO ICD-11 MMS simple tabulation (see docs/research/data-sources.md, section 1)."""
import re

RELEASE = "2026-01"
RELEASE_URL = f"https://icdcdn.who.int/static/releasefiles/{RELEASE}/"
CITATION = ("International Classification of Diseases, Eleventh Revision (ICD-11), World Health Organization "
            "(WHO) 2019 https://icd.who.int/browse11. Licensed under the Creative Commons "
            "Attribution-NoDerivatives 3.0 IGO licence (CC BY-ND 3.0 IGO).")

# A record starts where a line begins with a foundation URI (empty for residuals) and a release URI.
# Any other line continues the previous record: CodingNote can hold raw line breaks.
RECORD_START = re.compile(r"(http://id\.who\.int/\S*)?\thttp://id\.who\.int/icd/release/")
DEPTH_DASHES = re.compile(r"^(- )+")
VERSION = re.compile(r"Version:(.+)")


def unquote(field):
    if len(field) >= 2 and field[0] == field[-1] == '"':
        return field[1:-1].replace('""', '"')
    return field


def parse_tabulation(text):
    """Rows of the tabulation as dicts keyed by column name, with titles cleaned up."""
    lines = re.split(r"\r?\n", text.lstrip("﻿"))
    header = lines[0].split("\t")
    records = []
    for line in lines[1:]:
        if RECORD_START.match(line):
            records.append(line)
        elif records:
            records[-1] += "\n" + line
    rows = []
    for record in records:
        fields = record.split("\t")
        fields += [""] * (len(header) - len(fields))
        row = {name: unquote(value) for name, value in zip(header, fields)}
        row["Title"] = DEPTH_DASHES.sub("", row["Title"])
        rows.append(row)
    return rows


def tabulation_version(text):
    header = text.lstrip("﻿").split("\n", 1)[0]
    match = VERSION.search(header)
    return match.group(1).strip() if match else None
