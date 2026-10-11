# Model and data layouts

This document and the archive manifest cover the four entanglement HDF5 files.
Data for the other paper figures, including the DOS data underlying
Figs. 1(a) and 5, will be included in the same Zenodo upload; see the
[repository scope](../README.md).

## Dataset filenames

The generators and planned Zenodo upload use the descriptive names below.
The archive verifier also accepts the historical names, including the corrected
alias `entanglement_spectrum_1b.h5` for the original misspelled clean-spectrum file.

| Dataset filename | Historical filename |
| --- | --- |
| `clean_entanglement_spectrum.h5` | `entanglment_spectrum_1b.h5` |
| `disorder_entanglement_ensemble.h5` | `half_filling_data_20260519_134201.h5` |
| `example_entanglement_spectra.h5` | `entanglement_spectrum_1c.h5` |
| `mass_entanglement_ensemble.h5` | `half_filling_data_20260628_161626.h5` |

## Model

The clean Bloch Hamiltonian is

~~~text
H(k) = sin(k_x) sigma_x + sin(k_y) sigma_y
       + [-cos(k_z) - m_z + (2 - cos(k_x) - cos(k_y))] sigma_z.
~~~

The hopping parameters are `t=t_0=1` and `t_z=-1`. The cubic lattice has
periodic boundaries. The orbital/site index is
`orbital + 2*(x + L*(y + L*z))`, with two orbitals per site.
An independent site potential sampled uniformly from `[-W/2, W/2]` is added
identically to both orbitals of each site.

At zero temperature, the lowest `L^3` single-particle states are occupied.
The spatial subsystem keeps `x < L/2` and both orbitals. If `V_A` contains the
occupied eigenvectors restricted to that subsystem, the occupations are the sorted
eigenvalues of `V_A^dagger V_A`. Since the subsystem and occupied space have the
same dimension here, these are also the eigenvalues of `V_A V_A^dagger`.
The entropy is `-sum[xi*log2(xi) + (1-xi)*log2(1-xi)]`.
As in the legacy implementation, occupations within `1e-10` of zero or one
contribute zero to the entropy. Stored occupations are not rounded or clipped.

## Clean spectrum: clean_entanglement_spectrum.h5

| Dataset | Original shape | Meaning |
| --- | --- | --- |
| `eigvals` | `(3600, 60)` | 60 sorted occupations for each `(ky,kz)` block |

The original lattice size is `L=60`, with `W=m_z=0`.
Momentum indices run from zero to `L-1`, using `k=2*pi*index/L`.
Row `iy + L*iz` stores the `(ky,kz)` block. Reshaping to
`(L,L,L)` gives axes `(kz, ky, occupation)`; reshaping to `(L,-1)`
gives one row per `kz`.

The original file has no attributes. New files add model parameters, version and
axis-order attributes while keeping the dataset name and layout.
The historical filename and its corrected spelling are accepted aliases in the
archive manifest; all three names identify the same original bytes.
The similarly named historical file under the parent repository's `python_files/`
has shape `(10,10,10)` and is a different calculation; it is not part of the
four-file archive manifest.

## Disorder sweep: disorder_entanglement_ensemble.h5

| Dataset | Original shape | Meaning |
| --- | --- | --- |
| `eigvals` | `(10000,41,1000)` | realization, disorder point, sorted occupation |
| `data` | `(10000,41)` | von Neumann entanglement entropy in bits |
| `w_array` | `(41,)` | `linspace(0,8,41)` |

The cubic size is `L=10`; `m_z=0` is fixed by the legacy model and is not
stored in this original file. The original attributes are `Ns=10000`,
three false `obc_*` flags and a completion timestamp.
The timestamp in the historical filename was chosen before the long run; the stored
timestamp was written at completion.
New files also store the fixed mass grid and the additional generation metadata.
The file's historical location in the research workspace is
`half_filling_results/half_filling_data_20260519_134201.h5`; the download layout
places it next to the other three files without that directory prefix.

## Two-spectrum extract: example_entanglement_spectra.h5

| Dataset | Original shape | Meaning |
| --- | --- | --- |
| `eigvals` | `(2,1000)` | spectra at `W=0` and `W=2` |
| `w_array` | `(2,)` | `[0,2]` |

The rows equal `eigvals[0,0,:]` and `eigvals[0,10,:]` in the original
disorder sweep. They are individual spectra from realization zero, not disorder
averages. The original file has no attributes.
New extracts record the source basename, realization and parameter indices.
Extraction accepts both the old format without `mz_array` and the new
format, and requires the selected mass to be zero.

## Mass sweep: mass_entanglement_ensemble.h5

| Dataset | Original shape | Meaning |
| --- | --- | --- |
| `eigvals` | `(10000,41,1000)` | realization, mass point, sorted occupation |
| `data` | `(10000,41)` | von Neumann entanglement entropy in bits |
| `w_array` | `(41,)` | all values equal to 2 |
| `mz_array` | `(41,)` | `linspace(-2,0,41)` |

The cubic size is `L=10`. Original attributes include `Ns=10000`,
false `obc_*` flags, `t=t_0=1`, `t_z=-1`, and a completion timestamp.

## New generation metadata

New ensemble files preserve the existing field names, axis ordering and entropy
definition. Additional attributes record the lattice size, generator version,
seed, RNG policy, worker count, batch size, NumPy/h5py versions, model parameters
and UTC completion time. They are gzip-compressed in realization/parameter
chunks; compression does not change the stored numerical values.

The four original entanglement files are identified by the hashes in
[archived_data_manifest.json](../metadata/archived_data_manifest.json). Together they total
about 5.90 GB; the raw `eigvals` array of each ensemble contains 3.28 GB of
float64 values before compression.
