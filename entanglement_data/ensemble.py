"""Stream the disorder or mass ensemble to HDF5 in batches of realizations."""

from pathlib import Path

import numpy as np

from .backend import Model
from .io import lattice_size, model_attributes, new_h5

FILENAMES = {
    "w-sweep": "half_filling_data_20260519_134201.h5",
    "m-sweep": "half_filling_data_20260628_161626.h5",
}


def parameters(preset):
    if preset == "w-sweep":
        w = np.linspace(0.0, 8.0, 41)
        return w, np.zeros_like(w)
    if preset == "m-sweep":
        m = np.linspace(-2.0, 0.0, 41)
        return np.full_like(m, 2.0), m
    raise ValueError("Preset must be w-sweep or m-sweep")


def generate(preset, output=None, size=10, samples=10000, seed=1337,
             threads=1, batch_size=8, rng="task", library=None):
    size = lattice_size(size)
    w, m = parameters(preset)
    if samples < 1 or samples >= 2**31 or threads < 1 or batch_size < 1:
        raise ValueError("Samples, threads and batch size must be positive (samples < 2**31)")
    if not 0 <= seed < 2**64 or rng not in ("task", "legacy-thread"):
        raise ValueError("Seed must be a uint64 and RNG must be task or legacy-thread")
    output = Path(output) if output is not None else Path("data") / FILENAMES[preset]
    # Open the output first to reject existing files before building a model.
    with new_h5(output) as handle, Model(size, library) as model:
        modes = size**3
        es = handle.create_dataset(
            "eigvals", shape=(samples, len(w), modes), dtype="f8",
            chunks=(1, 1, modes), compression="gzip", compression_opts=4,
        )
        entropy = handle.create_dataset("data", shape=(samples, len(w)), dtype="f8")
        handle.create_dataset("w_array", data=w)
        handle.create_dataset("mz_array", data=m)
        handle.attrs.update({
            "Ns": samples,
            "preset": preset,
            "seed": seed,
            "rng": rng,
            "threads": threads,
            "batch_size": batch_size,
            "axis_order": "realization, parameter, sorted occupation",
            "entropy_log_base": 2,
            "entropy_endpoint_threshold": 1e-10,
            "archive_parameter_filename": FILENAMES[preset],
        })
        for first in range(0, samples, batch_size):
            count = min(batch_size, samples - first)
            s, xi = model.compute(w, m, first, count, seed, threads, rng)
            entropy[first:first + count] = s
            es[first:first + count] = xi
            print(f"Realizations complete: {first + count}/{samples}", flush=True)
        model_attributes(handle, size, "generate_half_filling.py")
    return output
