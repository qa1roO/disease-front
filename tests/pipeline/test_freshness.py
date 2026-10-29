import os
import tempfile
import unittest
from pathlib import Path

from pipeline.freshness import Stamps, is_up_to_date


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


class StampsTest(unittest.TestCase):
    """A fresh clone's mtimes are in checkout order, so a recorded stamp decides instead."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.src, self.out = self.dir / "in.txt", self.dir / "out.json"
        self.src.write_bytes(b"a\n")
        self.out.write_bytes(b"b\n")
        self.stamps = Stamps(self.dir / "stamps.json", self.dir)
        self.stamps.record("3", [self.out], [self.src])
        os.utime(self.src, (2000, 2000))
        os.utime(self.out, (1000, 1000))

    def test_matching_stamp_is_fresh_whatever_the_mtimes(self):
        self.assertTrue(Stamps(self.dir / "stamps.json", self.dir).is_up_to_date("3", [self.out], [self.src]))

    def test_crlf_checkout_still_matches(self):
        self.src.write_bytes(b"a\r\n")
        self.assertTrue(self.stamps.is_up_to_date("3", [self.out], [self.src]))

    def test_changed_input_is_stale(self):
        self.src.write_bytes(b"c\n")
        self.assertFalse(self.stamps.is_up_to_date("3", [self.out], [self.src]))

    def test_edited_output_is_stale(self):
        self.out.write_bytes(b"edited\n")
        self.assertFalse(self.stamps.is_up_to_date("3", [self.out], [self.src]))

    def test_new_file_in_an_input_folder_is_stale(self):
        folder = self.dir / "drafts"
        folder.mkdir()
        self.stamps.record("6", [self.out], [folder])
        (folder / "x.yaml").write_text("")
        self.assertFalse(self.stamps.is_up_to_date("6", [self.out], [folder]))

    def test_unstamped_stage_falls_back_to_mtimes(self):
        self.assertFalse(self.stamps.is_up_to_date("4", [self.out], [self.src]))


if __name__ == "__main__":
    unittest.main()
