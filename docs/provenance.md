# Source provenance and reproducibility

The selected source snapshots come from
[vimohr/master_project](https://github.com/vimohr/master_project). They were
collected locally before preparing this independent repository.
[historical_source_manifest.json](../metadata/historical_source_manifest.json) records their hashes
and distinguishes Git snapshots from the working-tree copies.
Some working-tree files contained changes that had not been committed. Only
the seven sources documenting these datasets and the supported backend are
included in `historical_sources/`.

## Source-to-dataset mapping

| Dataset | Evidence in the preserved sources |
| --- | --- |
| `clean_entanglement_spectrum.h5` at `L=60` | `historical_sources/clean_spectrum_calculation.py` contains the matching block calculation and HDF5 writer, both disabled in its current snapshot. |
| `disorder_entanglement_ensemble.h5` | `historical_sources/disorder_sweep_cdb8984.py` has the matching HDF5 format, although its saved parameter grid differs; `entanglement_backend_cdb8984.cpp` supplies the historical fixed-mass calculation. The exact producing revision is not recorded. |
| `example_entanglement_spectra.h5` | `historical_sources/spectrum_examples_and_plots.py` explicitly reads the original disorder-sweep filename and writes rows `[0,0]` and `[0,10]`. Both rows were verified against the original files. |
| `mass_entanglement_ensemble.h5` | `historical_sources/mass_sweep_cdf3307.py` uses `Ns=10000`, `W=2`, and the matching 41-point mass grid. The exact producing revision is not recorded. |

The [data layouts](data_layouts.md) map these descriptive dataset filenames to
the original archived filenames. Historical source filenames describe their
roles; the source manifest records their original paths and revisions.

The historical scripts contain disabled blocks, plots and paths intended for the
parent workspace. The supported top-level scripts supply the complete generation
interface, build instructions and command-line settings.

The exploratory notebooks and a later experimental wrapper were removed from
the current tree because their saved inputs and parameter grids describe other
runs. They remain available in earlier Git revisions of this repository.

## Numerical calculation

The clean spectrum generator uses the transverse-momentum decomposition in
`historical_sources/clean_spectrum_calculation.py`.
It constructs each `2L x 2L` Hamiltonian by the same Fourier convention, fills
exactly `L` orbitals and preserves the flattened block order.
Parentheses in the mass term preserve the legacy arithmetic grouping; changing
that grouping can change which nearly zero-energy state is occupied at a
degenerate Weyl-node momentum.

The new C++ kernel is derived from `historical_sources/entanglement_backend_working_tree.cpp`.
It retains the periodic-boundary Bloch/Fourier construction, the scalar site
disorder, the lowest-half occupation rule, the half-space cut, and the base-2
entropy with its endpoint threshold. Unrelated entropy-difference calculations
and open-boundary branches were removed because the archived datasets all use
periodic boundaries.

The new interface builds the clean Hamiltonian once, streams the ensemble to
HDF5 in batches, checks solver failures, and exposes a configurable seed.
It does not require a compiled library from the parent repository.
The default batch size is eight realizations; `--batch-size` controls the output
buffer. Each worker diagonalizes dense complex matrices of size up to
`2000 x 2000` for the archived `L=10` ensembles, so choose `--threads` to fit the
machine's memory. The complete output is published after all batches finish.

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
batch splitting. Archive checks cover altered spectra, incorrect parameter grids,
metadata, missing files, filename aliases and the original parent-workspace
layout. Source snapshots and the clean-spectrum reference fixture are checked
against their recorded hashes.

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

The original 12 numerical tests passed with Python 3.11.14 / NumPy 2.2.5 / h5py 3.13.0
and Python 3.14.2 / NumPy 2.5.3 / h5py 3.16.0. The local C++ build used
GNU C++ 14.2.0. GitHub Actions is configured to build and run the suite on Ubuntu
with Python 3.10, 3.11 and 3.14 and check the installed command-line entry points.

The expanded 17-test suite also passed in a clean source copy with a fresh C++
build and editable Python installation using Python 3.11.14 / NumPy 2.4.6 /
h5py 3.16.0. All four installed commands were exercised from outside that source
copy, including both small ensemble presets and extraction. All four original
archive files passed byte-size, SHA-256, schema, grid and attribute checks against
the manifest.
