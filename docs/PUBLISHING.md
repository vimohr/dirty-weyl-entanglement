# Code releases and Zenodo data

The code repository is
[vimohr/dirty-weyl-entanglement](https://github.com/vimohr/dirty-weyl-entanglement).
The data will be uploaded to a separate Zenodo dataset record.

## GitHub code repository

The code repository contains the generators, C++ backend, documentation, MIT
license, citation metadata, source snapshots and validation workflow. HDF5 files
and compiled binaries are excluded.

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

Create a dataset upload containing these original files:

| File to upload | Location relative to the original research workspace | Bytes |
| --- | --- | ---: |
| `entanglment_spectrum_1b.h5` | `entanglment_spectrum_1b.h5` | 1,730,048 |
| `entanglement_spectrum_1c.h5` | `entanglement_spectrum_1c.h5` | 18,064 |
| `half_filling_data_20260519_134201.h5` | `half_filling_results/half_filling_data_20260519_134201.h5` | 3,283,288,520 |
| `half_filling_data_20260628_161626.h5` | `half_filling_data_20260628_161626.h5` | 2,619,555,887 |

Include `metadata/archive_manifest.json`, `metadata/SHA256SUMS` and `docs/DATA.md` with the data
so the schema and checksums remain available independently of GitHub.
Preserve the original HDF5 bytes if using this manifest; recompressing or
rewriting a file changes its hash.
Upload each file directly under its basename so users can download all four into
one directory. The total HDF5 payload is 5,904,592,519 bytes (about 5.90 GB).
If correcting the 1b spelling to `entanglement_spectrum_1b.h5`, also change that
filename in the uploaded `SHA256SUMS`; the manifest verifier accepts either name.

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
> L=10 and W=2. The accompanying manifest lists SHA-256 hashes and dataset
> layouts. The linked code repository supplies generation commands and
> documents the distinction between original archived samples and newly
> seeded simulations.

Add the code repository URL under the record's related works or links, and
identify the code commit or release used for the documented method. Supply the
actual creators, affiliations and data license when preparing the record.
Also link the accompanying [paper](https://arxiv.org/abs/2607.26660), identified
by its DOI `10.48550/arXiv.2607.26660`.
`CITATION.cff` identifies the software; the dataset should receive its own
citation through the Zenodo record.

After reserving or publishing the actual record, update the two null fields in
`metadata/archive_manifest.json`, add the actual Zenodo link in `README.md`,
and add the GitHub repository/release link to the Zenodo record.
Commit these links and tag the release used for the data description.
Keep the dataset DOI separate from any future DOI for a software release.
No placeholder DOI is used by the generation or verification code.

## Verify the publication payload

Before publishing the original data, run:

~~~sh
python verify_archives.py --directory /path/to/the/four/files
git ls-files '*.h5' '*.hdf5' '*.so' '*.dylib' '*.dll' '*.pdf'
~~~

The first command must succeed; the second should print no files.
For the original workspace layout, use
`python verify_archives.py --directory .. --parent-layout`.
`--structure-only` skips the whole-file size and hash checks while still checking
dataset layouts, parameter grids and recorded attributes.

For a checksum-only check of a flat download with the original filenames, place
`SHA256SUMS` next to the HDF5 files and run:

~~~sh
sha256sum -c SHA256SUMS
~~~

For a new calculation, archive its outputs with a new manifest and describe
the recorded seed and generation settings instead of claiming the original
archive hashes.
