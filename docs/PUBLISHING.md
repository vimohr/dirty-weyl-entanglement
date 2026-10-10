# Publish the code and data

This folder is prepared as an independent local Git repository on branch
`main`. Its Git history is separate from the surrounding master-project
repository. No GitHub remote or Zenodo record is configured yet.

## GitHub code repository

1. Create an empty GitHub repository under the desired owner and name.
   The local repository already contains the README, license and ignore rules.
2. From this folder, add that repository as the remote and push:

~~~sh
git remote add origin git@github.com:YOUR_USER/YOUR_REPO.git
git push -u origin main
~~~

3. Check that the included GitHub Actions workflow succeeds on GitHub.
4. Tag the reviewed version and create its release:

~~~sh
git tag v0.1.0
git push origin v0.1.0
~~~

The code uses the selected MIT license. Generated HDF5 files and build products
are excluded from Git. The repository can also be registered as a submodule in
another project after its remote URL exists.

## Zenodo dataset record

Create a dataset upload containing these original files:

- `entanglment_spectrum_1b.h5`
- `half_filling_data_20260519_134201.h5`
- `entanglement_spectrum_1c.h5`
- `half_filling_data_20260628_161626.h5`

Include `metadata/archive_manifest.json` and `docs/DATA.md` with the data
so the schema and checksums remain available independently of GitHub.
Preserve the original HDF5 bytes if using this manifest; recompressing or
rewriting a file changes its hash.

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

After reserving or publishing the actual record, update the two null fields in
`metadata/archive_manifest.json`, add the actual Zenodo link in `README.md`,
and add the GitHub repository/release link to the Zenodo record.
Commit these links and tag the release used for the data description.
No placeholder DOI is used by the generation or verification code.

## Verify the publication payload

Before publishing the original data, run:

~~~sh
python verify_archives.py --directory /path/to/the/four/files
git ls-files '*.h5' '*.so' '*.pdf'
~~~

The first command must succeed; the second should print no files.
For a new calculation, archive its outputs with a new manifest and describe
the recorded seed and generation settings instead of claiming the original
archive hashes.
