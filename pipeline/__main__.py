"""Run pipeline stages: python -m pipeline <stage> [--force]

Stages: 1 (fetch ICD-11), 3 (build data/tree.json), 8 (build site/public/map.json), or all.
Each stage skips itself when its outputs are newer than its inputs.
"""
import argparse
import json
import sys
from pathlib import Path

from pipeline import fetch_icd11, icd11, site_data, tree
from pipeline.freshness import is_up_to_date

ROOT = Path(__file__).resolve().parent.parent
RAW_ICD11 = ROOT / "data" / "raw" / "icd11"
TABULATION = RAW_ICD11 / "tab" / "SimpleTabulation-ICD-11-MMS-en.txt"
MAPPING = RAW_ICD11 / "map" / "11To10MapToOneCategory.txt"
TREE = ROOT / "data" / "tree.json"
MAP = ROOT / "site" / "public" / "map.json"
PKG = Path(__file__).resolve().parent


def write_json(path, data, indent=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    separators = None if indent is not None else (",", ":")
    text = json.dumps(data, ensure_ascii=False, indent=indent, separators=separators)
    path.write_text(text + "\n", encoding="utf-8", newline="\n")


def stage1():
    fetch_icd11.fetch(RAW_ICD11)


def stage3():
    text = TABULATION.read_text(encoding="utf-8-sig")
    result = tree.build_tree(icd11.parse_tabulation(text), version=icd11.tabulation_version(text))
    write_json(TREE, result, indent=1)
    print(f"  {result['counts']}")


def stage8():
    write_json(MAP, site_data.build_map(json.loads(TREE.read_text(encoding="utf-8"))))


# number -> (name, run, inputs, outputs). A stage's own code counts as an input.
STAGES = {
    "1": ("fetch ICD-11", stage1, [], [TABULATION, MAPPING]),
    "3": ("build the tree", stage3, [TABULATION, PKG / "tree.py", PKG / "icd11.py"], [TREE]),
    "8": ("build site data", stage8, [TREE, PKG / "site_data.py"], [MAP]),
}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m pipeline", description=__doc__.splitlines()[0])
    parser.add_argument("stage", choices=[*STAGES, "all"])
    parser.add_argument("--force", action="store_true", help="run even if the outputs are up to date")
    args = parser.parse_args(argv)
    for number in STAGES if args.stage == "all" else [args.stage]:
        name, run, inputs, outputs = STAGES[number]
        if not args.force and is_up_to_date(outputs, inputs):
            print(f"stage {number} ({name}): up to date, skipped")
            continue
        print(f"stage {number} ({name})")
        run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
