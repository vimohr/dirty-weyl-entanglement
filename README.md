# Entanglement signatures of topological phase transitions in a dirty Weyl semimetal

Data generation scripts accompanying [arXiv:2607.26660](https://arxiv.org/abs/2607.26660)
by Vinícius Mohr, Shunji
Tsuchiya and András L. Szabó. The repository includes Python generators, an
Eigen/OpenMP backend, plotting scripts and metadata for the four original
entanglement HDF5 files.

**Zenodo dataset DOI:** [10.5281/zenodo.23300020](https://doi.org/10.5281/zenodo.23300020).
The HDF5 data record is separate from this code repository.

The generators focus on the paper's main topic, the entanglement spectrum.
The density of states (DOS) computations underlying Figs. 1(a) and 5 use
standard kernel polynomial methods (KPM; Appendix A). The corresponding
generation code is available on request. The Zenodo upload will include data
for all paper figures, including these DOS results. The [plotting guide](plotting/README.md)
maps the plotting functions to their figures, input files and numerical processing.

## Datasets

| Dataset filename | Command | Spectrum shape |
| --- | --- | --- |
| `clean_entanglement_spectrum.h5` | `python generate_clean_entanglement_spectrum.py` | `(3600, 60)` |
| `disorder_entanglement_ensemble.h5` | `python generate_entanglement_ensemble.py --preset w-sweep` | `(10000, 41, 1000)` |
| `example_entanglement_spectra.h5` | `python extract_example_entanglement_spectra.py` | `(2, 1000)` |
| `mass_entanglement_ensemble.h5` | `python generate_entanglement_ensemble.py --preset m-sweep` | `(10000, 41, 1000)` |

These descriptive names are the defaults for new calculations and the names
to use for the Zenodo upload. The archive verifier also accepts the historical
figure-based and timestamped filenames. See
[data layouts and parameters](docs/data_layouts.md) for the original-name mapping,
model and file schemas.

Fresh ensembles reproduce the model and parameter grids with a recorded seed.
The historical worker scheduling and exact software revisions are not fully
recorded, so use the Zenodo files for the exact original disorder samples.
See [provenance and reproducibility](docs/provenance.md).

## Install and build

Requirements: Linux, Python 3.10 or newer, a C++17 compiler, CMake, Eigen 3 and
OpenMP. NumPy and h5py are installed with the Python package.
On Ubuntu/Debian, install the build tools:

~~~sh
sudo apt-get update
sudo apt-get install -y python3-venv cmake g++ libeigen3-dev
~~~

Clone the repository and build:

~~~sh
git clone https://github.com/vimohr/dirty-weyl-entanglement.git
cd dirty-weyl-entanglement
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel 2
python -m unittest discover -s tests -v
~~~

Keep the editable installation so the compiled backend and archive manifest
remain available. It also installs `entanglement-clean`, `entanglement-ensemble`,
`entanglement-extract` and `entanglement-verify`. The tests use small calculations and
included reference values; the large HDF5 files are not required.
After updating a checkout, rerun `python -m pip install -e .` to refresh the
installed command names.

## Run a small example

These examples exercise all three generators with smaller lattices and ensembles:

~~~sh
python generate_clean_entanglement_spectrum.py --size 4 --output data/small_clean_spectrum.h5
python generate_entanglement_ensemble.py --preset w-sweep --size 4 --samples 2 --threads 2 --output data/small_disorder_ensemble.h5
python extract_example_entanglement_spectra.py --source data/small_disorder_ensemble.h5 --output data/small_example_spectra.h5
python generate_entanglement_ensemble.py --preset m-sweep --size 4 --samples 2 --threads 2 --output data/small_mass_ensemble.h5
~~~

## Generate the full datasets

The clean spectrum uses `L=60`. Each ensemble uses `L=10`, 10,000 realizations
and 41 parameter points, requiring 410,000 Hamiltonian diagonalizations and the
same number of correlation-matrix diagonalizations. These runs are intended for
a compute server; choose `--threads` to fit the available memory.

~~~sh
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
python generate_clean_entanglement_spectrum.py
python generate_entanglement_ensemble.py --preset w-sweep --samples 10000 --threads 8 --seed 1337
python extract_example_entanglement_spectra.py --source data/disorder_entanglement_ensemble.h5
python generate_entanglement_ensemble.py --preset m-sweep --samples 10000 --threads 8 --seed 1337
~~~

The disorder preset sweeps `W` from 0 to 8 at `m_z=0`; the mass preset sweeps
`m_z` from -2 to 0 at `W=2`. Both use periodic boundaries. Ensembles are written
in batches, and the default task RNG is independent of thread count and batch
size within the same compiled backend. Run a script with `--help` for all options.
Existing outputs are never overwritten; use `--output` for another calculation.

## Use the original archive

Download the four entanglement HDF5 files listed above from
[Zenodo](https://doi.org/10.5281/zenodo.23300020) into `data/`
and verify them against the recorded checksums, layouts, parameter grids
and attributes:

~~~sh
python verify_archived_data.py --directory data
~~~

To extract the exact spectra for panel 1c from the downloaded disorder ensemble:

~~~sh
python extract_example_entanglement_spectra.py --source data/disorder_entanglement_ensemble.h5 --output data/extracted_example_spectra.h5
~~~

This selects realization zero at `W=0` and `W=2`, without drawing new disorder.
New simulations have different metadata and samples, so they are not expected
to pass original-archive verification.

## Generate the plots

The scripts in `plotting/` generate Figs. 1(b), 1(c) and 2–6 from the archived
entanglement spectra and DOS tables. Plotting requires Python 3.10 or newer,
NumPy, h5py and Matplotlib. From the repository root, install the plotting
dependencies in your Python environment and run:

~~~sh
python -m pip install -r plotting/requirements.txt
python plotting/reconstruct_available_figures.py --root data --output data/reconstructed_figures
~~~

Place the inputs in `data/` using the filenames listed in the
[plotting guide](plotting/README.md). The guide includes a mapping from the
generator filenames, per-figure data fields, processing details and commands
for selecting figures and validating the inputs. The script saves PNG plots
and CSV tables; it reads the archived data directly and needs no C++ build.

## Reference

- [Plotting guide](plotting/README.md): figure functions, input filenames, numerical processing and output tables.
- [Data documentation](docs/data_layouts.md): model, parameters, dataset layouts and historical filenames.
- [Provenance](docs/provenance.md): source mapping, RNG policy and numerical validation.
- [Publication guide](docs/publishing.md): GitHub releases, Zenodo upload and checksum checks.
- [Historical sources](historical_sources/README.md): seven small source snapshots retained for provenance.
- [Archive manifest](metadata/archived_data_manifest.json) and [SHA256SUMS](metadata/SHA256SUMS): original-file checksums.

The code is licensed under [MIT](LICENSE). [CITATION.cff](CITATION.cff) supplies
software citation metadata. Cite the separate
[Zenodo dataset DOI](https://doi.org/10.5281/zenodo.23300020) when using the
archived HDF5 data, and the [paper](https://arxiv.org/abs/2607.26660) for the
scientific method.
