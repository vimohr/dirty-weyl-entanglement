#!/usr/bin/env python3
"""Validate stored arrays, parameter grids, and entropy units without changing data."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np

EXPECTED = {
    "half_filling_data_w_sweep_10000.h5": {"eigvals": (10000, 41, 1000), "data": (10000, 41), "w_array": (41,)},
    "half_filling_data_m_sweep_10000.h5": {"eigvals": (10000, 41, 1000), "data": (10000, 41), "w_array": (41,), "mz_array": (41,)},
    "clean_data_vs_mz.h5": {"eigvals": (1, 41, 1000), "data": (1, 41), "w_array": (41,), "mz_array": (41,)},
    "entanglement_spectrum_1b.h5": {"eigvals": (3600, 60)},
    "entanglement_spectrum_1c.h5": {"eigvals": (2, 1000), "w_array": (2,)},
}


def serializable(value):
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if hasattr(value, "tolist"):
        return value.tolist()
    return value


def entropy_nats(raw):
    x = np.clip(raw, 0, 1)
    result = np.zeros_like(x)
    positive = x > 0
    result[positive] = -x[positive] * np.log(x[positive])
    y = 1 - x
    positive = y > 0
    result[positive] -= y[positive] * np.log(y[positive])
    return result.sum(axis=-1)


def validate_hdf(path, expected, full, batch_size):
    result = {"bytes": path.stat().st_size, "datasets": {}, "errors": []}
    with h5py.File(path, "r") as f:
        result["attributes"] = {k: serializable(v) for k, v in f.attrs.items()}
        if set(f.keys()) != set(expected):
            result["errors"].append("Dataset names differ from the audited schema")
        for key, shape in expected.items():
            if key not in f:
                result["errors"].append(f"Missing dataset {key}")
                continue
            dataset = f[key]
            result["datasets"][key] = {"shape": list(dataset.shape), "dtype": str(dataset.dtype)}
            if tuple(dataset.shape) != shape:
                result["errors"].append(f"Unexpected shape for {key}: {dataset.shape}")
        if result["errors"]:
            return result
        # Every small observable and every parameter axis is checked in both modes.
        for key in expected:
            if key in {"eigvals", "es_kykz", "xi"}:
                continue
            a = f[key][:]
            if not np.all(np.isfinite(a)):
                result["errors"].append(f"Nonfinite values in {key}")
        if path.name == "half_filling_data_w_sweep_10000.h5":
            axes_ok = np.allclose(f["w_array"][:], np.arange(41) * 0.2, rtol=0, atol=1e-12)
        elif path.name in {"half_filling_data_m_sweep_10000.h5", "clean_data_vs_mz.h5"}:
            ww = 2 if path.name.startswith("half") else 0
            axes_ok = (np.allclose(f["mz_array"][:], np.linspace(-2, 0, 41), rtol=0, atol=1e-12)
                       and np.allclose(f["w_array"][:], ww, rtol=0, atol=1e-12))
        elif path.name == "entanglement_spectrum_1c.h5":
            axes_ok = np.allclose(f["w_array"][:], [0, 2], rtol=0, atol=1e-12)
        else:
            axes_ok = True
        if not axes_ok:
            result["errors"].append("Unexpected parameter grid")
        key = "eigvals" if "eigvals" in f else ("es_kykz" if "es_kykz" in f else "xi")
        n = f[key].shape[0]
        check_all = full or int(np.prod(f[key].shape)) <= 1_000_000
        ranges = [(first, min(first + batch_size, n)) for first in range(0, n, batch_size)] if check_all else [(0, 8), (n // 2, n // 2 + 8), (n - 8, n)]
        checked = nonfinite = outside = unsorted = tiny_outside = 0
        low, high, max_entropy_error = float("inf"), float("-inf"), 0.0
        for first, last in ranges:
            a = f[key][first:last]
            checked += a.size
            nonfinite += int(np.count_nonzero(~np.isfinite(a)))
            outside += int(np.count_nonzero((a < -1e-10) | (a > 1 + 1e-10)))
            tiny_outside += int(np.count_nonzero((a < 0) | (a > 1)))
            unsorted += int(np.count_nonzero(np.any(np.diff(a, axis=-1) < -1e-10, axis=-1)))
            low, high = min(low, float(np.min(a))), max(high, float(np.max(a)))
            if key == "eigvals" and "data" in f:
                stored = f["data"][first:last] * np.log(2)
                max_entropy_error = max(max_entropy_error, float(np.max(np.abs(stored - entropy_nats(a)))))
        result["spectrum_checks"] = {
            "dataset": key, "mode": "full" if check_all else "sampled",
            "eigenvalues_checked": int(checked), "range": [low, high],
            "nonfinite": nonfinite, "outside_0_1_beyond_1e_10": outside,
            "outside_0_1_including_roundoff": tiny_outside, "unsorted_spectra": unsorted,
        }
        if key == "eigvals" and "data" in f:
            result["max_stored_entropy_bits_error_nats"] = max_entropy_error
            if max_entropy_error > 1e-6:
                result["errors"].append("Stored data no longer match entropy in bits")
        if nonfinite or outside or unsorted:
            result["errors"].append("Spectrum validation failed")
    return result


def validate_dos(root):
    expected = {f"dos_m{m / 10:.1f}_W{w / 10:.1f}.dat" for m in range(-20, 1) for w in range(2, 61)}
    present = {p.name for p in (root / "DoS_data").glob("*.dat")}
    result = {"expected_files": len(expected), "files_present": len(present), "rows_checked": 0,
              "missing": sorted(expected - present), "unexpected": sorted(present - expected),
              "invalid": [], "files_with_negative_DOS": 0}
    low, high = float("inf"), float("-inf")
    for name in sorted(present):
        try:
            a = np.loadtxt(root / "DoS_data" / name)
            if a.shape != (201, 2) or not np.all(np.isfinite(a)) or not np.allclose(a[:, 0], np.linspace(-2, 2, 201), rtol=0, atol=1e-12):
                result["invalid"].append(name)
                continue
            result["rows_checked"] += len(a)
            result["files_with_negative_DOS"] += int(np.any(a[:, 1] < 0))
            low, high = min(low, float(a[:, 1].min())), max(high, float(a[:, 1].max()))
        except (ValueError, OSError):
            result["invalid"].append(name)
    result["DOS_range"] = [low, high] if result["rows_checked"] else None
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--full", action="store_true", help="Read every eigenvalue; default samples large spectra")
    parser.add_argument("--batch-size", type=int, default=313)
    parser.add_argument("--hash", action="store_true", help="Record SHA-256 of original data files")
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("Batch size must be positive")
    report = {"full_requested": args.full, "hdf5": {}, "dos": validate_dos(args.root)}
    failed = bool(report["dos"]["missing"] or report["dos"]["unexpected"] or report["dos"]["invalid"])
    for name, expected in EXPECTED.items():
        path = args.root / name
        if not path.exists():
            report["hdf5"][name] = {"errors": ["File missing"]}
            failed = True
            continue
        item = validate_hdf(path, expected, args.full, args.batch_size)
        report["hdf5"][name] = item
        failed |= bool(item["errors"])
        print(f"{name}: {'FAIL' if item['errors'] else 'PASS'}", flush=True)
    if args.hash:
        report["sha256"] = {}
        for path in sorted([*(args.root / "DoS_data").glob("*.dat"), *(args.root / n for n in EXPECTED if (args.root / n).is_file())]):
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
                    digest.update(block)
            report["sha256"][path.relative_to(args.root).as_posix()] = digest.hexdigest()
    report["numerical_validation_passed"] = not failed
    out = args.output or args.root / "audit" / "validation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Numerical validation {'passed' if not failed else 'FAILED'}; report: {out}")
    print("Validation checks numerical integrity; figure interpretation is documented separately.")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
