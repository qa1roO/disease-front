from pathlib import Path


def is_up_to_date(outputs, inputs):
    """True when every output exists and is no older than every input."""
    outputs, inputs = [Path(p) for p in outputs], [Path(p) for p in inputs]
    if not all(p.exists() for p in outputs) or not all(p.exists() for p in inputs):
        return False
    if not inputs:
        return True
    return min(p.stat().st_mtime for p in outputs) >= max(p.stat().st_mtime for p in inputs)
