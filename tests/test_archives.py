"""Archive validation failures and integrity of preserved source evidence."""

import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import h5py
import numpy as np

from verify_archives import verify

ROOT = Path(__file__).resolve().parent.parent


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self.tmp.name)
        self.path = self.directory / "archive.h5"
        with h5py.File(self.path, "w") as handle:
            handle["eigvals"] = np.zeros((1, 2, 8), dtype="f8")
            handle["w_array"] = np.array([0, 2], dtype="f8")
            handle.attrs["Ns"] = 1
        self.record = {
            "filename": self.path.name,
            "filename_aliases": ["corrected_name.h5"],
            "source_path_in_parent": "half_filling_results/archive.h5",
            "size_bytes": self.path.stat().st_size,
            "sha256": hashlib.sha256(self.path.read_bytes()).hexdigest(),
            "datasets": {
                "eigvals": {"shape": [1, 2, 8], "dtype": "float64"},
                "w_array": {"shape": [2], "dtype": "float64"},
            },
            "parameters": {"w_array": [0, 2]},
            "attributes": {"Ns": 1},
        }

    def tearDown(self):
        self.tmp.cleanup()

    def check_archive(self, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return verify(self.directory, {"files": [self.record]}, **kwargs)

    def test_bytes_alias_and_parent_layout(self):
        self.assertEqual(self.check_archive(), [])
        corrected = self.path.with_name("corrected_name.h5")
        self.path.rename(corrected)
        self.assertEqual(self.check_archive(), [])
        original = self.directory / self.record["source_path_in_parent"]
        original.parent.mkdir()
        corrected.rename(original)
        self.assertEqual(self.check_archive(parent_layout=True), [])

    def test_same_layout_with_wrong_grid_or_attributes_is_rejected(self):
        with h5py.File(self.path, "r+") as handle:
            handle["w_array"][1] = 3
            handle.attrs["Ns"] = 2
        failures = self.check_archive(structure_only=True)
        self.assertTrue(any("parameter grid w_array" in failure for failure in failures))
        self.assertTrue(any("attribute Ns" in failure for failure in failures))

    def test_changed_spectrum_is_detected_by_hash(self):
        with h5py.File(self.path, "r+") as handle:
            handle["eigvals"][0, 0, 0] = 0.5
        self.assertEqual(self.check_archive(structure_only=True), [])
        self.assertTrue(any("SHA-256" in failure for failure in self.check_archive()))

    def test_group_instead_of_dataset_and_missing_file_are_reported(self):
        with h5py.File(self.path, "r+") as handle:
            del handle["eigvals"]
            handle.create_group("eigvals")
        self.assertTrue(any("dataset eigvals" in failure
                            for failure in self.check_archive(structure_only=True)))
        self.path.unlink()
        self.assertTrue(self.check_archive()[0].startswith("Missing "))

    def test_preserved_source_and_reference_hashes_match_metadata(self):
        sources = json.loads((ROOT / "metadata/source_snapshots.json").read_text())
        for source in sources["snapshots"]:
            with self.subTest(file=source["file"]):
                actual = hashlib.sha256((ROOT / "legacy" / source["file"]).read_bytes()).hexdigest()
                self.assertEqual(actual, source["sha256"])
        archive = json.loads((ROOT / "metadata/archive_manifest.json").read_text())
        fixture = json.loads((ROOT / "tests/fixtures/clean_archive_blocks.json").read_text())
        clean = next(record for record in archive["files"]
                     if record["filename"] == fixture["source_file"])
        self.assertEqual(fixture["source_sha256"], clean["sha256"])
        expected_sums = "".join(f"{record['sha256']}  {record['filename']}\n"
                                for record in archive["files"])
        self.assertEqual((ROOT / "metadata/SHA256SUMS").read_text(), expected_sums)


if __name__ == "__main__":
    unittest.main()
