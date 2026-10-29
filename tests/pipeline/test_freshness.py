import os
import tempfile
import unittest
from pathlib import Path

from pipeline.freshness import is_up_to_date


class FreshnessTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.src = self.dir / "in.txt"
        self.out = self.dir / "out.json"
        self.src.write_text("x")

    def touch(self, path, mtime):
        path.write_text("x")
        os.utime(path, (mtime, mtime))

    def test_missing_output_is_stale(self):
        self.assertFalse(is_up_to_date([self.out], [self.src]))

    def test_output_newer_than_inputs_is_fresh(self):
        self.touch(self.src, 1000)
        self.touch(self.out, 2000)
        self.assertTrue(is_up_to_date([self.out], [self.src]))

    def test_output_older_than_an_input_is_stale(self):
        self.touch(self.out, 1000)
        self.touch(self.src, 2000)
        self.assertFalse(is_up_to_date([self.out], [self.src]))

    def test_missing_input_is_stale(self):
        self.touch(self.out, 2000)
        self.assertFalse(is_up_to_date([self.out], [self.dir / "gone.txt"]))

    def test_no_inputs_means_existing_outputs_are_fresh(self):
        self.touch(self.out, 2000)
        self.assertTrue(is_up_to_date([self.out], []))


if __name__ == "__main__":
    unittest.main()
