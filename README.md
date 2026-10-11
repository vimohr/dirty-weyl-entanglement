# Entanglement signatures of topological phase transitions in a dirty Weyl semimetal

Data generation scripts accompanying the paper by Vinícius Mohr, Shunji
Tsuchiya and András L. Szabó.

This repository generates the HDF5 datasets used for the clean and disordered
entanglement spectra. It includes the Python entry points, the Eigen/OpenMP
calculation, preserved source snapshots, and a manifest of the original data.
The large HDF5 files belong in a separate Zenodo dataset record.

**Zenodo record: pending publication.** No DOI has been assigned to this repository.
The `zenodo_doi` and `zenodo_record_url` fields in
[metadata/archive_manifest.json](metadata/archive_manifest.json) are currently null.
Once the record is published, its link should be added here.

## Datasets

| Original filename | Generation command | Original spectrum shape |
| --- | --- | --- |
| `entanglment_spectrum_1b.h5` | `python generate_1b.py` | `(3600, 60)` |
| `half_filling_data_20260519_134201.h5` | `python generate_half_filling.py --preset w-sweep` | `(10000, 41, 1000)` |
| `entanglement_spectrum_1c.h5` | `python extract_1c.py` | `(2, 1000)` |
| `half_filling_data_20260628_161626.h5` | `python generate_half_filling.py --preset m-sweep` | `(10000, 41, 1000)` |

The missing second “e” in `entanglment_spectrum_1b.h5` is the spelling of the
original archive file and is retained for compatibility. The verifier also
accepts the corrected spelling, `entanglement_spectrum_1b.h5`, if that is the
name used in the Zenodo upload. Renaming the file preserves its checksum.
The original May ensemble lives at
`half_filling_results/half_filling_data_20260519_134201.h5` in the research
workspace; the Zenodo download layout uses its basename directly in `data/`.
The filename timestamps identify the original datasets; they are not the dates
of new calculations.

The published archive will supply the exact data used in the figures.
Fresh disorder simulations use the same model and parameter grids, with a
reproducible task seed by default. The historical thread scheduling and exact
software revisions are not fully recorded, so fresh simulations are not claimed
to recreate the archived disorder samples bit for bit. See
[provenance](docs/PROVENANCE.md) and the [file schemas](docs/DATA.md).

## Install and build

The supported build target is Linux with Python 3.10 or newer, NumPy, h5py,
a C++17 compiler, CMake, Eigen 3, and OpenMP. On Ubuntu/Debian, install the build
tools with:

~~~sh
sudo apt-get update
sudo apt-get install -y python3-venv cmake g++ libeigen3-dev
~~~

Clone the repository, then install and build from its root:

~~~sh
git clone https://github.com/vimohr/dirty-weyl-entanglement.git
cd dirty-weyl-entanglement
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel 2
python -m unittest discover -s tests -v
~~~

The tests compare the C++ spectrum against a small independent NumPy calculation,
check the clean spectrum against archived reference blocks, exercise both ensemble
presets and extraction, and check reproducibility across worker counts and batches.
They also check archive verification and the integrity of the preserved source
snapshots. They do not require the large archive files.

All scripts can be run directly; an editable installation is optional:

~~~sh
python -m pip install -e .
~~~

That also installs `entanglement-1b`, `entanglement-ensemble`,
`entanglement-1c`, and `entanglement-verify`. Keep this as an editable/source
installation so the locally compiled backend and archive manifest remain available.

## Run a small example

These commands generate small examples with the same file layouts. Their lattice
size and number of realizations differ from the archived data.

~~~sh
python generate_1b.py --size 4 --output data/smoke_1b.h5
python generate_half_filling.py --preset w-sweep --size 4 --samples 2 --threads 2 --output data/smoke_w.h5
python extract_1c.py --source data/smoke_w.h5 --output data/smoke_1c.h5
python generate_half_filling.py --preset m-sweep --size 4 --samples 2 --threads 2 --output data/smoke_m.h5
~~~

## Generate the full datasets

The clean calculation resolves transverse-momentum blocks at `L=60`.
The ensembles use `L=10`, 10,000 realizations and 41 parameter points.
Each ensemble therefore requires 410,000 dense Hamiltonian and correlation-matrix
diagonalizations and is intended for a compute server. Each worker holds dense
complex matrices of size up to `2000 x 2000`; choose the worker count to fit the
machine's memory.

~~~sh
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
python generate_1b.py
python generate_half_filling.py --preset w-sweep --samples 10000 --threads 8 --seed 1337
python extract_1c.py --source data/half_filling_data_20260519_134201.h5
python generate_half_filling.py --preset m-sweep --samples 10000 --threads 8 --seed 1337
~~~

The disorder preset fixes `m_z=0` and uses
`W = linspace(0, 8, 41)`. The mass preset fixes `W=2` and uses
`m_z = linspace(-2, 0, 41)`. Both use periodic boundaries in all directions.

Ensembles are written in batches, with eight realizations per batch by default.
`--batch-size` changes the output-buffer size. The clean Hamiltonian is built
once and shared between workers. An output is published only after all batches
finish, and an existing output file is never overwritten.
Use `--output` to choose another filename for an additional calculation.

The default `--rng task` seeds each realization and parameter pair separately.
Changing the number of worker threads or the batch size leaves the draws
unchanged with the same compiled backend. `--rng legacy-thread` follows the
historical thread-seeded policy; it depends on thread count, scheduling and batch
boundaries and does not recover the unidentified scheduling of the archived runs.
Compiler, standard-library and numerical-library differences can also change
results. Clean zero modes can depend on numerical choices at degeneracies.

## Use the original archive

After the Zenodo record is published, download the four HDF5 files into `data/`
with the filenames listed above. Verify them with:

~~~sh
python verify_archives.py --directory data
~~~

The verifier checks file sizes, SHA-256 hashes, dataset shapes, dtypes, parameter
grids and recorded attributes against the originals in the manifest.
`--structure-only` skips the byte-size and hash checks; it still checks the grids
and recorded attributes. Newly generated files have new metadata and disorder
samples, so they are not expected to pass original-archive verification.

To check the originals in the parent research workspace without copying the
large files, run this from the repository root:

~~~sh
python verify_archives.py --directory .. --parent-layout
~~~

For a checksum-only check of a flat download with the original filenames,
download `SHA256SUMS` from Zenodo alongside the HDF5 files and run
`sha256sum -c SHA256SUMS` in that directory. The checksum file is also provided
in [metadata/SHA256SUMS](metadata/SHA256SUMS).

To recover the exact two spectra shown in panel 1c from a downloaded disorder
ensemble:

~~~sh
python extract_1c.py --source data/half_filling_data_20260519_134201.h5 --output data/extracted_1c.h5
~~~

This reads only `eigvals[0, 0, :]` and `eigvals[0, 10, :]`, corresponding to
`W=0` and `W=2` in realization zero. No new random draw is involved.

## Repository contents

- `generate_1b.py`, `generate_half_filling.py`, `extract_1c.py`: supported generators.
- `entanglement_data/`: model, HDF5 and backend interfaces.
- `cpp/half_filling.cpp`: the included C++ calculation.
- `legacy/`: original scripts and notebooks, preserved as source snapshots.
- `metadata/`: archive hashes, schemas and source snapshot hashes.
- `tests/`: small numerical and file-format regression checks.
- `docs/`: model, provenance and GitHub/Zenodo publication instructions.

Data files, build products, virtual environments and generated figures are ignored
by Git. The source repository is licensed under [MIT](LICENSE).
See [the publication guide](docs/PUBLISHING.md) for the remaining record links and
release steps.

## Citation

[CITATION.cff](CITATION.cff) supplies the software citation metadata displayed by
GitHub. Cite the separate Zenodo dataset DOI when using the archived HDF5 data,
and this code repository when describing the generation method. The dataset DOI
will be linked here after the data upload is available.
