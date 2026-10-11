# Code releases and Zenodo data

The code repository is
[vimohr/dirty-weyl-entanglement](https://github.com/vimohr/dirty-weyl-entanglement).
The data will be uploaded to a separate Zenodo dataset record:
[10.5281/zenodo.23300020](https://doi.org/10.5281/zenodo.23300020).

## GitHub code repository

The code repository contains the generators, C++ backend, plotting scripts,
documentation, MIT license, citation metadata, source snapshots and validation
workflow. HDF5 files and compiled binaries are excluded.

Push reviewed commits from the repository root:

~~~sh
git push origin main
~~~

Check that the included GitHub Actions workflow succeeds, then tag the version
used for the Zenodo description and create a GitHub release:

~~~sh
git tag v0.1.0
git push origin v0.1.0
~~~

The MIT license covers the code. Choose the dataset license explicitly when
preparing the Zenodo record.

## Zenodo dataset record

Prepare the dataset upload for this record with these original entanglement files:

| File to upload | Location relative to the original research workspace | Bytes |
| --- | --- | ---: |
| `clean_entanglement_spectrum.h5` | `entanglment_spectrum_1b.h5` | 1,730,048 |
| `example_entanglement_spectra.h5` | `entanglement_spectrum_1c.h5` | 18,064 |
| `disorder_entanglement_ensemble.h5` | `half_filling_results/half_filling_data_20260519_134201.h5` | 3,283,288,520 |
| `mass_entanglement_ensemble.h5` | `half_filling_data_20260628_161626.h5` | 2,619,555,887 |

Include the data for the remaining paper figures in the same record, including
the DOS data underlying Figs. 1(a) and 5, computed using standard kernel
polynomial methods (KPM). The repository focuses on entanglement data
generation; the corresponding KPM generation code is available on request.
Include `plotting/README.md` as the file-to-figure guide. It describes the plotting
functions, input filenames, units, numerical processing and output tables.

Include `metadata/archived_data_manifest.json`, `metadata/SHA256SUMS` and `docs/data_layouts.md` with the data
so the schema and checksums remain available independently of GitHub.
Preserve the original HDF5 bytes if using this manifest; recompressing or
rewriting a file changes its hash.
Upload each original file under the descriptive name in the first column so
users can download all four into one directory. Renaming a file preserves its
bytes and checksum. These four entanglement files total 5,904,592,519 bytes
(about 5.90 GB); this excludes the additional figure data.
`SHA256SUMS` uses these descriptive names. The manifest verifier also accepts
the historical filenames recorded in `filename_aliases`.

Use Zenodo's
[new-upload documentation](https://help.zenodo.org/docs/deposit/create-new-upload/)
to fill in the dataset title, creators, description and data license.
The selected MIT license covers the code repository; choose the dataset license
explicitly in the record metadata.
Zenodo lets an uploader
[reserve a DOI before publication](https://help.zenodo.org/docs/deposit/describe-records/reserve-doi/).
The DOI is registered when the record is published.

Suggested record description:

> HDF5 entanglement occupations and von Neumann entropies for a two-orbital
> disordered-semimetal model with periodic boundaries and a half-space
> entanglement cut. The record contains the clean momentum-resolved spectrum
> at L=60, a 10,000-realization disorder sweep at L=10 and m_z=0, its
> two-spectrum W=0/W=2 extract, and a 10,000-realization mass sweep at
> L=10 and W=2. The record also includes data for the remaining paper figures,
> including the DOS data underlying Figs. 1(a) and 5, computed using standard
> kernel polynomial methods (KPM). The corresponding generation code is available
> on request. The plotting guide maps the archived data to Figs. 1(b), 1(c) and
> 2–6 and describes the commands and numerical processing used to generate them.
> The accompanying manifest lists SHA-256 hashes and dataset layouts for the
> four entanglement files.
> The linked code repository supplies entanglement generation commands and
> plotting scripts and documents the distinction between original archived
> samples and newly seeded simulations.

Add the code repository URL under the record's related works or links, and
identify the code commit or release used for the documented method. Supply the
actual creators, affiliations and data license when preparing the record.
Also link the accompanying [paper](https://arxiv.org/abs/2607.26660), identified
by its DOI `10.48550/arXiv.2607.26660`.
`CITATION.cff` identifies the software; the dataset should receive its own
citation through the Zenodo record.

The dataset DOI and record URL are recorded in
`metadata/archived_data_manifest.json`, with the DOI also linked in `README.md`
and recorded in `CITATION.cff`. Add the GitHub repository/release link to the
Zenodo record and tag the release used for the data description.
Keep the dataset DOI separate from any future DOI for a software release.
No placeholder DOI is used by the generation or verification code.

## Verify the publication payload

Before publishing the original data, run:

~~~sh
python verify_archived_data.py --directory /path/to/the/four/files
git ls-files '*.h5' '*.hdf5' '*.so' '*.dylib' '*.dll' '*.pdf'
~~~

The first command verifies the four entanglement files and must succeed;
the second should print no files. These checks do not cover the additional
figure data, which should have their own checksums and layout descriptions
in the Zenodo record.
For the original workspace layout, use
`python verify_archived_data.py --directory .. --parent-layout`.
`--structure-only` skips the whole-file size and hash checks while still checking
dataset layouts, parameter grids and recorded attributes.

For a checksum-only check of a flat download with the published filenames, place
`SHA256SUMS` next to the HDF5 files and run:

~~~sh
sha256sum -c SHA256SUMS
~~~

For a new calculation, archive its outputs with a new manifest and describe
the recorded seed and generation settings instead of claiming the original
archive hashes.
