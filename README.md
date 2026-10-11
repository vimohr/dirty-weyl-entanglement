# Entanglement signatures of topological phase transitions in a dirty Weyl semimetal

Data generation scripts accompanying [arXiv:2607.26660](https://arxiv.org/abs/2607.26660)
by Vinícius Mohr, Shunji
Tsuchiya and András L. Szabó. The repository includes Python generators, an
Eigen/OpenMP backend and metadata for the four original entanglement HDF5 files.

**Zenodo data record: pending publication.** The HDF5 files will be uploaded separately
from the code; their DOI and download link will be added here when available.

The generators focus on the paper's main topic, the entanglement spectrum.
The density of states (DOS) computations underlying Figs. 1(a) and 5 use
standard kernel polynomial methods (KPM; Appendix A). The corresponding
generation code is available on request. The Zenodo upload will include data
for all paper figures, including these DOS results, to support
reproducing every plot with simple postprocessing and plotting.

## Datasets

| Original filename | Command | Spectrum shape |
| --- | --- | --- |
| `entanglment_spectrum_1b.h5` | `python generate_1b.py` | `(3600, 60)` |
| `half_filling_data_20260519_134201.h5` | `python generate_half_filling.py --preset w-sweep` | `(10000, 41, 1000)` |
| `entanglement_spectrum_1c.h5` | `python extract_1c.py` | `(2, 1000)` |
| `half_filling_data_20260628_161626.h5` | `python generate_half_filling.py --preset m-sweep` | `(10000, 41, 1000)` |

The original 1b filename contains a spelling error. Verification also accepts
`entanglement_spectrum_1b.h5`. The filename timestamps identify the archived
runs; new calculations keep those default names for compatibility.
See [data layouts and parameters](docs/DATA.md) for the model and file schemas.

Fresh ensembles reproduce the model and parameter grids with a recorded seed.
The historical worker scheduling and exact software revisions are not fully
recorded, so use the Zenodo files for the exact original disorder samples.
See [provenance and reproducibility](docs/PROVENANCE.md).

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
remain available. It also installs `entanglement-1b`, `entanglement-ensemble`,
`entanglement-1c` and `entanglement-verify`. The tests use small calculations and
included reference values; the large HDF5 files are not required.

## Run a small example

These examples exercise all three generators with smaller lattices and ensembles:

~~~sh
python generate_1b.py --size 4 --output data/smoke_1b.h5
python generate_half_filling.py --preset w-sweep --size 4 --samples 2 --threads 2 --output data/smoke_w.h5
python extract_1c.py --source data/smoke_w.h5 --output data/smoke_1c.h5
python generate_half_filling.py --preset m-sweep --size 4 --samples 2 --threads 2 --output data/smoke_m.h5
~~~

## Generate the full datasets

The clean spectrum uses `L=60`. Each ensemble uses `L=10`, 10,000 realizations
and 41 parameter points, requiring 410,000 Hamiltonian diagonalizations and the
same number of correlation-matrix diagonalizations. These runs are intended for
a compute server; choose `--threads` to fit the available memory.

~~~sh
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
python generate_1b.py
python generate_half_filling.py --preset w-sweep --samples 10000 --threads 8 --seed 1337
python extract_1c.py --source data/half_filling_data_20260519_134201.h5
python generate_half_filling.py --preset m-sweep --samples 10000 --threads 8 --seed 1337
~~~

The disorder preset sweeps `W` from 0 to 8 at `m_z=0`; the mass preset sweeps
`m_z` from -2 to 0 at `W=2`. Both use periodic boundaries. Ensembles are written
in batches, and the default task RNG is independent of thread count and batch
size within the same compiled backend. Run a script with `--help` for all options.
Existing outputs are never overwritten; use `--output` for another calculation.

## Use the original archive

Download the four entanglement HDF5 files listed above from Zenodo into `data/`
and verify them against the recorded checksums, layouts, parameter grids
and attributes:

~~~sh
python verify_archives.py --directory data
~~~

To extract the exact spectra for panel 1c from the downloaded disorder ensemble:

~~~sh
python extract_1c.py --source data/half_filling_data_20260519_134201.h5 --output data/extracted_1c.h5
~~~

This selects realization zero at `W=0` and `W=2`, without drawing new disorder.
New simulations have different metadata and samples, so they are not expected
to pass original-archive verification.

## Reference

- [Data documentation](docs/DATA.md): model, parameters, dataset layouts and historical filenames.
- [Provenance](docs/PROVENANCE.md): source mapping, RNG policy and numerical validation.
- [Publication guide](docs/PUBLISHING.md): GitHub releases, Zenodo upload and checksum checks.
- [Historical sources](legacy/README.md): seven small source snapshots retained for provenance.
- [Archive manifest](metadata/archive_manifest.json) and [SHA256SUMS](metadata/SHA256SUMS): original-file checksums.

The code is licensed under [MIT](LICENSE). [CITATION.cff](CITATION.cff) supplies
software citation metadata. Cite the separate Zenodo dataset DOI when using the
archived HDF5 data, and the [paper](https://arxiv.org/abs/2607.26660) for the
scientific method.
