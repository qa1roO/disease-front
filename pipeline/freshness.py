"""When a stage can skip itself.

A fresh clone gives every file the checkout time as its mtime, in no useful order, so mtimes alone would rerun
stages whose committed outputs are fine (stage 7 then spends ten minutes on ClinicalTrials.gov). Each run records
a stamp, the content hashes of the stage's inputs and outputs, in the committed data/stamps.json; a stage is up to
date when its stamp still matches. Stages with no stamp yet fall back to mtimes.
"""
import hashlib
import json
from pathlib import Path


def is_up_to_date(outputs, inputs):
    """True when every output exists and is no older than every input."""
    outputs, inputs = [Path(p) for p in outputs], [Path(p) for p in inputs]
    if not all(p.exists() for p in outputs) or not all(p.exists() for p in inputs):
        return False
    if not inputs:
        return True
    return min(p.stat().st_mtime for p in outputs) >= max(p.stat().st_mtime for p in inputs)


def content_hash(path):
    """A file's hash with line endings normalised (git may check text out as CRLF), a folder's sorted file names,
    or None when the path is missing."""
    path = Path(path)
    if path.is_dir():
        return "dir:" + ",".join(sorted(p.name for p in path.iterdir()))
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:16]


def stamp(paths, root):
    return {Path(p).relative_to(root).as_posix(): content_hash(p) for p in paths}


class Stamps:
    """data/stamps.json: stage -> {path relative to the repo root: content hash}, for its inputs and outputs."""

    def __init__(self, path, root):
        self.path, self.root = Path(path), Path(root)
        self.data = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}

    def is_up_to_date(self, stage, outputs, inputs):
        if not all(Path(p).exists() for p in outputs):
            return False
        if stage not in self.data:
            return is_up_to_date(outputs, inputs)
        return self.data[stage] == stamp([*inputs, *outputs], self.root)

    def record(self, stage, outputs, inputs):
        self.data[stage] = stamp([*inputs, *outputs], self.root)
        self.path.write_text(json.dumps(self.data, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
