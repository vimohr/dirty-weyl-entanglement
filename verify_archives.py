#!/usr/bin/env python3
"""Verify downloaded archive files against the recorded original bytes and shapes."""

import argparse
import hashlib
import json
from pathlib import Path

import h5py


def verify(directory, manifest, structure_only=False):
    failures = []
    for record in manifest["files"]:
        path = Path(directory) / record["filename"]
        if not path.is_file():
            failures.append(f"Missing {path}")
            continue
        try:
            with h5py.File(path, "r") as handle:
                for name, field in record["datasets"].items():
                    if name not in handle or list(handle[name].shape) != field["shape"]:
                        failures.append(f"{path.name}: incorrect shape or missing dataset {name}")
                    elif str(handle[name].dtype) != field["dtype"]:
                        failures.append(f"{path.name}: incorrect dtype for {name}")
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
    args = parser.parse_args()
    with open(args.manifest) as stream:
        manifest = json.load(stream)
    failures = verify(args.directory, manifest, args.structure_only)
    if failures:
        parser.exit(1, "\n".join(failures) + "\n")
    print("All archive files verified.")


if __name__ == "__main__":
    main()
