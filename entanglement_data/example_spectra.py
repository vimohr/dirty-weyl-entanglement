"""Extract the two occupations arrays plotted in panel 1c without loading an ensemble."""

from pathlib import Path

import h5py
import numpy as np

from .hdf5_io import new_h5


def extract(source, output="data/example_entanglement_spectra.h5", realization=0):
    source = Path(source)
    with h5py.File(source, "r") as original:
        if "eigvals" not in original or "w_array" not in original:
            raise ValueError("Input must contain eigvals and w_array")
        eigvals = original["eigvals"]
        if eigvals.ndim != 3:
            raise ValueError("Input eigvals must have shape (realizations, parameters, modes)")
        if realization < 0 or realization >= eigvals.shape[0]:
            raise ValueError("Realization index is outside the ensemble")
        w = original["w_array"][:]
        if w.shape != (eigvals.shape[1],):
            raise ValueError("w_array does not match the parameter axis")
        # The oldest disorder-sweep file did not store its fixed m_z=0.
        mass = original["mz_array"][:] if "mz_array" in original else np.zeros_like(w)
        if mass.shape != w.shape:
            raise ValueError("mz_array does not match w_array")
        indices = []
        for disorder in (0.0, 2.0):
            matches = np.flatnonzero(np.isclose(w, disorder, atol=1e-12, rtol=0)
                                    & np.isclose(mass, 0.0, atol=1e-12, rtol=0))
            if len(matches) != 1:
                raise ValueError(f"Input must contain exactly one W={disorder}, m_z=0 entry")
            indices.append(int(matches[0]))
        rows = np.stack([eigvals[realization, index, :] for index in indices])
    with new_h5(output) as handle:
        handle.create_dataset("eigvals", data=rows)
        handle.create_dataset("w_array", data=np.array([0.0, 2.0]))
        handle.attrs["generator"] = "extract_example_spectra.py"
        handle.attrs["source_file"] = source.name
        handle.attrs["source_realization"] = realization
        handle.attrs["source_parameter_indices"] = indices
        handle.attrs["fixed_m_z"] = 0.0
    return output
