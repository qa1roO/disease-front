"""Count Disease Map provinces in the ICD-11 MMS simple tabulation.

One-off research script for ticket 01 (see data-sources.md). Not part of the pipeline.

Usage:
    python -I count_provinces.py <SimpleTabulation-ICD-11-MMS-en.txt> <11To10MapToOneCategory.txt>

Both files come from https://icdcdn.who.int/static/releasefiles/2026-01/
(SimpleTabulation-ICD-11-MMS-en.zip and mapping.zip).

Province = a non-residual category with no children, in a kept chapter.
Residual = IsResidual is True (the ".Y other specified" / ".Z unspecified" entries).
"""
import collections
import re
import sys

# Non-disease chapters (CONTEXT.md, "Scope"): symptoms, injury, external causes,
# factors influencing health, special purposes, traditional medicine, functioning, extension codes.
EXCLUDED_CHAPTERS = {"21", "22", "23", "24", "25", "26", "V", "X"}
CATEGORY_CODE = re.compile(r"[A-Z][0-9]{2}(\.[0-9X]+)?")
BLOCK_RANGE = re.compile(r"[A-Z][0-9]{2}-[A-Z][0-9]{2}")


def read_tabulation(path):
    # Tab-separated, but CodingNote can contain raw line breaks, so a record starts only
    # where a line begins with an (optional, empty for residuals) foundation URI + release URI.
    lines = re.split(r"\r?\n", open(path, encoding="utf-8-sig", newline="").read())
    header = lines[0].split("\t")
    records = []
    for line in lines[1:]:
        if re.match(r"(http://id\.who\.int/\S*)?\thttp://id\.who\.int/icd/release/", line):
            records.append(line)
        elif records:
            records[-1] += "\n" + line
    rows = []
    for record in records:
        fields = record.split("\t")
        fields += [""] * (len(header) - len(fields))
        row = dict(zip(header, fields))
        row["Title"] = row["Title"].strip('"')
        rows.append(row)
    return rows


def read_icd11_to_icd10(path):
    mapping = {}
    with open(path, encoding="utf-8-sig") as f:
        header = f.readline().rstrip("\r\n").split("\t")
        for line in f:
            row = dict(zip(header, line.rstrip("\r\n").split("\t")))
            # The mapping file's URIs carry the release (".../11/2026-01/mms/..."), the tabulation's don't.
            uri = re.sub(r"/11/\d{4}-\d{2}/", "/11/", row["Linearization (release) URI"])
            mapping[uri] = row["icd10Code"].strip()
    return mapping


def main(tabulation_path, mapping_path):
    rows = read_tabulation(tabulation_path)
    children = collections.defaultdict(list)
    for row in rows:
        children[row["Parent"]].append(row)

    def is_residual(row):
        return row["IsResidual"] == "True"

    def is_leaf(row):
        return row["isLeaf"] == "True"

    print("rows", len(rows), dict(collections.Counter(r["ClassKind"] for r in rows)))
    titles = {r["ChapterNo"]: r["Title"] for r in rows if r["ClassKind"] == "chapter"}
    per_chapter = collections.defaultdict(collections.Counter)
    for row in rows:
        stats = per_chapter[row["ChapterNo"]]
        if row["ClassKind"] == "block":
            stats["blocks"] += 1
        elif row["ClassKind"] == "category":
            stats["categories"] += 1
            if is_residual(row):
                stats["residual"] += 1
            elif is_leaf(row):
                stats["provinces"] += 1

    print(f"{'ch':>3} {'cats':>6} {'resid':>6} {'prov':>6} {'blocks':>6}  title")
    kept_total = collections.Counter()
    for ch in sorted(per_chapter, key=lambda c: (not c.isdigit(), c)):
        stats = per_chapter[ch]
        excluded = ch in EXCLUDED_CHAPTERS
        if not excluded:
            kept_total.update(stats)
        print(f"{ch:>3} {stats['categories']:>6} {stats['residual']:>6} {stats['provinces']:>6} "
              f"{stats['blocks']:>6}  {titles.get(ch, '?')}{' (excluded)' if excluded else ''}")
    print("KEPT", dict(kept_total))

    kept = [r for r in rows if r["ChapterNo"] not in EXCLUDED_CHAPTERS]
    provinces = [r for r in kept if r["ClassKind"] == "category" and not is_residual(r) and is_leaf(r)]
    # A category whose only children are residuals would become a leaf once they are removed.
    promoted = [r for r in kept if r["ClassKind"] == "category" and not is_residual(r) and not is_leaf(r)
                and all(is_residual(k) for k in children[r["Foundation URI"]])]
    print("provinces", len(provinces), "+ categories with only residual children:", len(promoted))
    unflagged = [r for r in provinces if re.search(r"unspecified|other specified", r["Title"], re.I)]
    print("provinces titled 'unspecified'/'other specified' but not flagged residual:", len(unflagged))

    territories = [r for r in kept if r["ClassKind"] != "chapter" and not is_residual(r) and not is_leaf(r)]
    mixed = 0
    for parent in [r for r in kept if not is_residual(r) and not is_leaf(r)]:
        kids = [k for k in children[parent["Foundation URI"]] if not is_residual(k)]
        if any(is_leaf(k) for k in kids) and any(not is_leaf(k) for k in kids):
            mixed += 1
    print("territories below chapter:", len(territories),
          "(blocks", sum(r["ClassKind"] == "block" for r in territories),
          ", non-leaf categories", sum(r["ClassKind"] == "category" for r in territories), ")")
    print("parents with both province and territory children:", mixed)
    print("max territory nesting (title dashes):", max(r["Title"].count("- ") for r in territories))

    mapping = read_icd11_to_icd10(mapping_path)
    targets = [mapping.get(r["Linearization URI"], "") for r in provinces]
    print("provinces with an ICD-10 target:", sum(bool(t) for t in targets), "of", len(provinces))
    print("  -> ICD-10 category:", sum(bool(CATEGORY_CODE.fullmatch(t)) for t in targets),
          " -> ICD-10 block range:", sum(bool(BLOCK_RANGE.fullmatch(t)) for t in targets),
          " -> ICD-10 chapter only:",
          sum(bool(t) and not CATEGORY_CODE.fullmatch(t) and not BLOCK_RANGE.fullmatch(t) for t in targets))
    print("  distinct ICD-10 targets:", len(set(targets)))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
