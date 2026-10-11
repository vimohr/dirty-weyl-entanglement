#!/usr/bin/env python3
"""Verify original archive bytes, dataset layouts, parameter grids and attributes."""

import argparse
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np


def verify(directory, manifest, structure_only=False, parent_layout=False):
    failures = []
    for record in manifest["files"]:
        if parent_layout:
            names = [record["source_path_in_parent"]]
        else:
            names = [record["filename"], *record.get("filename_aliases", [])]
        paths = [Path(directory) / name for name in names]
        path = next((candidate for candidate in paths if candidate.is_file()), paths[0])
        if not path.is_file():
            failures.append(f"Missing {path}")
            continue
        try:
            with h5py.File(path, "r") as handle:
                for name, field in record["datasets"].items():
                    dataset = handle.get(name)
                    if not isinstance(dataset, h5py.Dataset) or list(dataset.shape) != field["shape"]:
                        failures.append(f"{path.name}: incorrect shape or missing dataset {name}")
                    elif str(dataset.dtype) != field["dtype"]:
                        failures.append(f"{path.name}: incorrect dtype for {name}")
                for name, values in record.get("parameters", {}).items():
                    dataset = handle.get(name)
                    if isinstance(dataset, h5py.Dataset) and not np.array_equal(dataset[...], values):
                        failures.append(f"{path.name}: incorrect parameter grid {name}")
                for name, value in record.get("attributes", {}).items():
                    if name not in handle.attrs or not np.array_equal(handle.attrs[name], value):
                        failures.append(f"{path.name}: missing or incorrect attribute {name}")
            if not structure_only:
                if path.stat().st_size != record["size_bytes"]:
                    failures.append(f"{path.name}: file size differs from archive")
                sha = hashlib.sha256()
                with path.open("rb") as stream:
                    for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
                        sha.update(block)
                if sha.hexdigest() != record["sha256"]:
                    failures.append(f"{path.name}: SHA-256 differs from archive")
        except OSError as error:
            failures.append(f"{path.name}: {error}")
        print(f"Checked {path.name}", flush=True)
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", default="data", help="Folder containing the four original HDF5 files")
    parser.add_argument("--manifest", default=str(Path(__file__).parent / "metadata/archive_manifest.json"))
    parser.add_argument("--structure-only", action="store_true", help="Skip whole-file SHA-256 and byte-size checks")
    parser.add_argument("--parent-layout", action="store_true",
                        help="Use source_path_in_parent, including the historical half_filling_results/ folder")
    args = parser.parse_args()
    try:
        with open(args.manifest) as stream:
            manifest = json.load(stream)
        failures = verify(args.directory, manifest, args.structure_only, args.parent_layout)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    if failures:
        parser.exit(1, "\n".join(failures) + "\n")
    print("All archive files verified.")


if __name__ == "__main__":
    main()
