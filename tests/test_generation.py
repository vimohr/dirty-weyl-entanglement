"""Small numerical and file-format checks; no archived datasets are needed."""

import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import h5py
import numpy as np

from entanglement_data.backend import Model
from entanglement_data.clean import block_spectrum, generate as generate_clean
from entanglement_data.ensemble import generate as generate_ensemble
from entanglement_data.extract import extract
from entanglement_data.io import new_h5

ROOT = Path(__file__).resolve().parent.parent


def reference_full_spectrum(size, mass):
    """Independent full Fourier-space calculation for comparison with the C++ cut."""
    k = 2 * np.pi * np.arange(size) / size
    sx = np.array([[0, 1], [1, 0]], dtype=complex)
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sz = np.diag([1, -1])
    h = np.zeros((2 * size**3, 2 * size**3), dtype=complex)
    for iz, kz in enumerate(k):
        for iy, ky in enumerate(k):
            for ix, kx in enumerate(k):
                q = 2 * (ix + size * (iy + size * iz))
                h[q:q + 2, q:q + 2] = (
                    np.sin(kx) * sx + np.sin(ky) * sy
                    + (-np.cos(kz) - mass + (2 - np.cos(kx) - np.cos(ky))) * sz
                )
    indices = np.arange(size)
    dft = np.exp(-2j * np.pi * np.outer(indices, indices) / size) / np.sqrt(size)
    f = np.kron(np.kron(np.kron(dft, dft), dft), np.eye(2))
    _, vectors = np.linalg.eigh(f.conj().T @ h @ f)
    mask = ((np.arange(2 * size**3) // 2) % size) < size // 2
    restricted = vectors[mask, :size**3]
    return np.linalg.eigvalsh(restricted @ restricted.conj().T)


class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_clean_blocks_agree_with_full_model(self):
        # A nonzero generic mass avoids ambiguities from degenerate zero modes.
        for size in (2, 4):
            values = np.sort(np.concatenate([
                block_spectrum(size, iy, iz, mass=0.37)
                for iz in range(size) for iy in range(size)
            ]))
            np.testing.assert_allclose(values, reference_full_spectrum(size, 0.37), atol=2e-12)

    def test_clean_blocks_agree_with_archived_reference(self):
        fixture = json.loads((ROOT / "tests/fixtures/clean_archive_blocks.json").read_text())
        for block in fixture["blocks"]:
            actual = block_spectrum(fixture["size"], block["iy"], block["iz"], fixture["mass"])
            np.testing.assert_allclose(actual, block["eigvals"], atol=1e-10, rtol=0)

    def test_clean_layout_and_physical_bounds(self):
        path = self.directory / "clean.h5"
        with contextlib.redirect_stdout(io.StringIO()):
            generate_clean(4, mass=0.37, output=path)
        with h5py.File(path) as f:
            self.assertEqual(f["eigvals"].shape, (16, 4))
            np.testing.assert_allclose(f["eigvals"][2 + 4 * 3], block_spectrum(4, 2, 3, 0.37))
            values = f["eigvals"][:]
            self.assertGreaterEqual(values.min(), -1e-12)
            self.assertLessEqual(values.max(), 1 + 1e-12)
            self.assertTrue(np.all(np.diff(values, axis=1) >= -1e-12))

    def test_cpp_clean_agrees_with_full_model(self):
        for size in (2, 4):
            with Model(size) as model:
                entropy, values = model.compute([0], [0.37])
            np.testing.assert_allclose(values[0, 0], reference_full_spectrum(size, 0.37), atol=2e-12)
            p = np.clip(values[0, 0], 0, 1)
            p = p[(p > 1e-10) & (p < 1 - 1e-10)]
            expected = -np.sum(p * np.log2(p) + (1 - p) * np.log2(1 - p))
            self.assertAlmostEqual(entropy[0, 0], expected, places=12)

    def test_task_rng_independent_of_threads_and_batches(self):
        with Model(2) as model:
            one = model.compute([0, 2], [0.37, 0.37], count=3, seed=42, threads=1)
            two = model.compute([0, 2], [0.37, 0.37], count=3, seed=42, threads=2)
            first = model.compute([0, 2], [0.37, 0.37], first=0, count=1, seed=42)
            rest = model.compute([0, 2], [0.37, 0.37], first=1, count=2, seed=42)
            changed = model.compute([0, 2], [0.37, 0.37], count=3, seed=43)
        for component in range(2):
            np.testing.assert_array_equal(one[component], two[component])
            np.testing.assert_array_equal(
                one[component], np.concatenate([first[component], rest[component]])
            )
        self.assertFalse(np.allclose(one[1][:, 1], changed[1][:, 1]))
        self.assertGreaterEqual(one[1].min(), -1e-12)
        self.assertLessEqual(one[1].max(), 1 + 1e-12)

    def test_legacy_rng_can_run_with_one_thread(self):
        with Model(2) as model:
            _, values = model.compute([0, 2], [0, 0], rng="legacy-thread", threads=1)
        self.assertEqual(values.shape, (1, 2, 8))
        self.assertTrue(np.all(np.isfinite(values)))

    def test_ensemble_presets_and_extract(self):
        for preset in ("w-sweep", "m-sweep"):
            path = self.directory / f"{preset}.h5"
            with contextlib.redirect_stdout(io.StringIO()):
                generate_ensemble(preset, path, size=2, samples=2, threads=2, batch_size=1)
            with h5py.File(path) as f:
                self.assertEqual(f["eigvals"].shape, (2, 41, 8))
                self.assertEqual(f["data"].shape, (2, 41))
                if preset == "w-sweep":
                    self.assertEqual(f["w_array"][10], 2)
                    np.testing.assert_array_equal(f["mz_array"][:], np.zeros(41))
                else:
                    np.testing.assert_array_equal(f["w_array"][:], np.full(41, 2))
                    np.testing.assert_allclose(f["mz_array"][:], np.linspace(-2, 0, 41))
        output = self.directory / "extract.h5"
        extract(self.directory / "w-sweep.h5", output, realization=1)
        with h5py.File(self.directory / "w-sweep.h5") as source, h5py.File(output) as f:
            np.testing.assert_array_equal(f["eigvals"][0], source["eigvals"][1, 0])
            np.testing.assert_array_equal(f["eigvals"][1], source["eigvals"][1, 10])
            np.testing.assert_array_equal(f["w_array"][:], [0, 2])

    def test_extract_supports_old_file_without_mass(self):
        source = self.directory / "legacy.h5"
        values = np.linspace(0, 1, 2 * 41 * 8).reshape(2, 41, 8)
        with h5py.File(source, "w") as f:
            f["eigvals"] = values
            f["w_array"] = np.linspace(0, 8, 41)
        output = self.directory / "small.h5"
        extract(source, output)
        with h5py.File(output) as f:
            np.testing.assert_array_equal(f["eigvals"][:], values[0, [0, 10]])

    def test_invalid_extraction_has_no_output(self):
        source = self.directory / "bad.h5"
        with h5py.File(source, "w") as f:
            f["eigvals"] = np.zeros((1, 3, 8))
            f["w_array"] = [0, 2, 2]
        output = self.directory / "unwritten.h5"
        with self.assertRaises(ValueError):
            extract(source, output)
        self.assertFalse(output.exists())

    def test_existing_output_is_preserved_and_failed_write_is_removed(self):
        output = self.directory / "existing.h5"
        output.write_bytes(b"existing data")
        with self.assertRaises(FileExistsError):
            with new_h5(output):
                pass
        self.assertEqual(output.read_bytes(), b"existing data")
        failed = self.directory / "failed.h5"
        with self.assertRaises(RuntimeError):
            with new_h5(failed) as handle:
                handle["data"] = [1]
                raise RuntimeError("intentional interrupted generation")
        self.assertFalse(failed.exists())
        self.assertEqual(list(self.directory.glob("*.partial")), [])

    def test_bad_sizes_rejected(self):
        with self.assertRaises(ValueError):
            block_spectrum(3, 0, 0)
        with self.assertRaises(ValueError):
            Model(1)

    def test_cli_runs_from_outside_the_repository(self):
        output = self.directory / "cli.h5"
        result = subprocess.run(
            [sys.executable, str(ROOT / "generate_1b.py"), "--size", "2",
             "--output", str(output)],
            cwd=self.directory, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        with h5py.File(output) as f:
            self.assertEqual(f["eigvals"].shape, (4, 2))


if __name__ == "__main__":
    unittest.main()
