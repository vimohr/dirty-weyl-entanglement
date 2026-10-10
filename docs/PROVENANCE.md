# Source provenance and reproducibility

The source snapshots come from
[vimohr/master_project](https://github.com/vimohr/master_project). They were
collected locally before preparing this independent repository.
[source_snapshots.json](../metadata/source_snapshots.json) records their hashes
and distinguishes Git snapshots from the working-tree copies.
Some working-tree files contained changes that had not been committed.

## Source-to-dataset mapping

| Dataset | Evidence in the preserved sources |
| --- | --- |
| `entanglment_spectrum_1b.h5` at `L=60` | `legacy/quickie.py` contains the matching block calculation and HDF5 writer, both disabled in its current snapshot. |
| `half_filling_data_20260519_134201.h5` | `legacy/run_half_filling_cdb8984.py` has the matching HDF5 format, although its saved parameter grid differs; `testvi_cpp_cdb8984.cpp` supplies the historical fixed-mass calculation. The exact producing revision is not recorded. |
| `entanglement_spectrum_1c.h5` | `legacy/quick_plot.py` explicitly reads that disorder-sweep filename and writes rows `[0,0]` and `[0,10]`. Both rows were verified against the original files. |
| `half_filling_data_20260628_161626.h5` | `legacy/run_half_filling_cdf3307.py` uses `Ns=10000`, `W=2`, and the matching 41-point mass grid. The exact producing revision is not recorded. |

`legacy/quick_check.ipynb` also writes the 1c filename, but its currently saved
input is another, later dataset. A filename alone does not identify the producing
run. `legacy/testvi.ipynb` also writes the 1b filename; its currently saved
lattice is different from the archived `L=60` calculation.

The legacy notebooks and scripts are evidence, rather than the supported
generation interface: they contain disabled blocks, intermediate plots,
assertions used to stop experiments, and paths intended for the parent workspace.
The supported top-level scripts remove those execution dependencies and supply
the missing build instructions and command-line settings.

## Numerical calculation

The new 1b generator uses the transverse-momentum decomposition in `quickie.py`.
It constructs each `2L x 2L` Hamiltonian by the same Fourier convention, fills
exactly `L` orbitals and preserves the flattened block order.
Parentheses in the mass term preserve the legacy arithmetic grouping; changing
that grouping can change which nearly zero-energy state is occupied at a
degenerate Weyl-node momentum.

The new C++ kernel is derived from `legacy/testvi_cpp_current.cpp`.
It retains the periodic-boundary Bloch/Fourier construction, the scalar site
disorder, the lowest-half occupation rule, the half-space cut, and the base-2
entropy with its endpoint threshold. Unrelated entropy-difference calculations
and open-boundary branches were removed because the archived datasets all use
periodic boundaries.

The new interface builds the clean Hamiltonian once, streams the ensemble to
HDF5 in batches, checks solver failures, and exposes a configurable seed.
It does not require a compiled library from the parent repository.

## Random draws

The historical implementation seeds a thread-local `std::mt19937` with
`1337 + omp_get_thread_num()` and uses a dynamically scheduled OpenMP loop.
A realization receives the next draws from whichever worker executes it.
The original worker counts, scheduling and precise library builds are not
recorded in the HDF5 metadata.

The new default RNG constructs a fresh `std::mt19937` for each
`(realization, parameter)` task, using `std::seed_seq` with four uint32 words:
`[seed_low, seed_high, realization, parameter]`.
The disorder remains uniform on `[-W/2,W/2]` and identical on both orbitals
of a site. Worker count and batch size do not change those draws within the same
compiled backend. Cross-toolchain identity is not promised:
`std::uniform_real_distribution`, eigensolvers and near-degenerate states
can differ between implementations.

`--rng legacy-thread` retains a sequence per worker seeded with `seed+thread`.
It offers the old random-number policy, but a new task schedule and batching
still do not identify or recreate the original disorder realization.
Use the archived Zenodo files whenever exact original samples are needed.

## Checks performed

The test suite compares small clean spectra to an independent full NumPy
calculation, checks an archived sample of the 1b blocks, checks the two preset
grids and HDF5 layouts, and exercises extraction and output protection.
It also verifies that task-based generation is unchanged by worker count and
batch splitting.

During preparation, the complete `L=60` spectrum was regenerated. All 3,600
blocks, including the projected Weyl-node blocks, matched the existing archive
within `4e-15` after preserving the legacy arithmetic grouping.
Extracting 1c from the original disorder ensemble reproduced both archived
occupation arrays exactly. The `L=10` clean 1c spectrum matched the union
of clean momentum blocks within `8e-14`. Selected entropies from both
archived ensembles agreed with the stored occupations within `1e-13`.
These checks support the model and data mapping; they do not establish recovery
of every historical random draw.

The full 10,000-realization ensembles were not rerun while preparing the
repository. The provided examples and tests use small lattices and ensembles.

The 12 automated tests passed with Python 3.11.14 / NumPy 2.2.5 / h5py 3.13.0
and Python 3.14.2 / NumPy 2.5.3 / h5py 3.16.0. The local C++ build used
GNU C++ 14.2.0. GitHub Actions is configured to build and run the small suite
on Ubuntu with Python 3.11 after the repository is published.
