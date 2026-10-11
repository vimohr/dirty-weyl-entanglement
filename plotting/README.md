# Plotting paper figures

`reconstruct_available_figures.py` generates Figs. 1(b), 1(c) and 2–6 of
*Entanglement signatures of topological phase transitions in a dirty Weyl
semimetal* from the [Zenodo datasets](https://doi.org/10.5281/zenodo.23300020).
It reads the archived entanglement eigenvalues and DOS tables and saves PNG
plots together with CSV tables of the processed observables.

## Install and run

Plotting requires Python 3.10 or newer, NumPy, h5py and Matplotlib. From the
repository root, create or activate a Python environment and install:

~~~sh
python -m pip install -r plotting/requirements.txt
~~~

Put the inputs listed below in one directory, with the DOS tables in its
`DoS_data/` subdirectory. Generate the figures with:

~~~sh
python plotting/reconstruct_available_figures.py --root data --output data/reconstructed_figures
~~~

`--root` selects the data directory, defaulting to the repository's `data/`
directory. `--output` selects the output directory;
its default is `reconstructed_figures/` inside the data directory. Select
individual figures with `--figures`, for example:

~~~sh
python plotting/reconstruct_available_figures.py --root data --figures 1b 1c
python plotting/reconstruct_available_figures.py --root data --figures 3 6 --batch-size 64
~~~

The default batch size is 313 realizations. Lower it to reduce memory use when
processing the ensembles. The scripts run directly from the checkout and need
no C++ build.

## Figures, functions and inputs

| Figure | Function | Input file and fields | Processing |
| --- | --- | --- | --- |
| 1(b) | `figure1b` | `clean_entanglement_spectrum.h5`: `eigvals` | Reshape the `(3600, 60)` clean spectrum to `(kz, ky, occupation)` for `L=60`, center the momentum grid on zero and plot the occupations against `kz`. |
| 1(c) | `figure1c` | `example_entanglement_spectra.h5`: `eigvals`, `w_array` | Plot sorted occupations with zero-based indices 485–515 for `W=0` and the stored `W=2` realization. |
| 2 | `edos` | `disorder_entanglement_ensemble.h5`: `eigvals`, `w_array` | Pool eigenvalues across realizations at `W=1, 2, 3, 3.8, 4.4` and compute normalized EDOS histograms on `[0, 1]`. |
| 3 | `entropy_figures` | `disorder_entanglement_ensemble.h5`: `eigvals`, `w_array` | Compute disorder-averaged entropies of orders 1, 2 and 3, shade the mean plus/minus population variance and plot the local exponents of their changes from `W=0`. |
| 4 | `edos` | `mass_entanglement_ensemble.h5`: `eigvals`, `mz_array` | Compute normalized EDOS histograms at `m=0, -0.6, -1.1, -1.2, -1.6` in the fixed-`W=2` mass sweep. |
| 5 | `figure5` | `DoS_data/dos_m{m:.1f}_W{W:.1f}.dat`: energy and average DOS columns | Plot the DOS against energy for the `m=0` disorder sweep and the `W=2` mass sweep. |
| 6 | `entropy_figures` | `disorder_entanglement_ensemble.h5`: `eigvals`, `w_array` | Compute disorder-averaged Rényi entropies of orders 10, 20, 30, 40 and 50 and their local exponents. |

The four entanglement input filenames match the generator defaults in the
[repository dataset table](../README.md#datasets) and archive manifest.
Download the files into `data/` under these names.

For Fig. 5(a), the script selects `m=0` and
`W=1, 2, 3, 3.5, 3.6, 3.7, 3.8, 3.9, 4, 4.1`. For Figs. 5(b) and 5(c), it
selects `W=2` and respectively `m=0, -0.6, -0.7, -0.8, -0.9` and
`m=-1, -1.1, -1.2, -1.3, -1.4, -1.5, -1.6`. Filenames use one decimal place,
for example `DoS_data/dos_m0.0_W2.0.dat`. The two columns contain `E/t` and
the average DOS.

## Numerical processing and outputs

The EDOS density in each bin is its count divided by the total number of
eigenvalues at that parameter point and the bin width, so the histogram
integrates to one. Fig. 2 uses 119 bins and Fig. 4 uses 100 bins by default;
change them with `--bins2` and `--bins4`.
The logarithmic EDOS axis spans `1e-3` to `100` in Fig. 2 and `1e-4` to `100`
in Fig. 4, matching the paper's displayed ranges.

Entropies are calculated from `eigvals` using natural logarithms, giving values
in nats. Order 1 is the von Neumann entropy; the other orders use
`S_q = sum(log(xi**q + (1-xi)**q)) / (1-q)`. The stored HDF5 `data` field contains
the von Neumann entropy in bits. For each order, the script computes the mean,
population variance and standard error across realizations. It obtains the
local exponent using `numpy.gradient` on `log(mean_S(W) - mean_S(0))` against
`log(W)` for positive disorder strengths and positive entropy differences.

Plots are saved as `figure1b.png`, `figure1c.png` and `figure2.png` through
`figure6.png`. The associated tables are:

- `figure1c.csv`: the plotted spectral indices and occupations.
- `figure2_histograms.csv` and `figure4_histograms.csv`: parameter values, bin
  edges, counts and normalized densities.
- `entropy_statistics.csv`: means, population variances, standard errors and
  local exponents for all eight entropy orders. This table is written when
  either Fig. 3 or Fig. 6 is requested.
- `figure5_dos.csv`: panel, mass, disorder, energy and average DOS.

## Validate the inputs

`validate_data.py` checks HDF5 shapes, parameter grids, finite values, sorted
occupations and consistency between the stored entropies and the spectra. It
also checks the DOS tables for the grid `m=-2` to `0` and `W=0.2` to `6`, both
in steps of `0.1`. In addition to the four entanglement inputs above, validation
expects `clean_data_vs_mz.h5`, containing `eigvals`, `data`, `w_array` and
`mz_array` for the clean mass sweep.

~~~sh
python plotting/validate_data.py --root data --output data/validation.json
~~~

The default mode samples the large spectra and checks the smaller arrays in
full. Add `--full` to read every eigenvalue and `--hash` to record SHA-256 hashes
of the input files in the JSON report.

## Figure checks

Figs. 1(b), 1(c) and 2–6 were generated using the original spectra, the complete
10,000-realization disorder and mass ensembles, and the archived DOS tables,
then compared visually with the accompanying paper. The spectral features,
EDOS peak evolution, entropy curves and DOS trends agree with the paper;
colors, markers, typography and line interpolation can differ.

Full numerical validation checked every eigenvalue in both ensembles and all
1,239 DOS tables. The four original entanglement files retain their recorded
SHA-256 hashes. Each EDOS histogram retains all 10,000,000 eigenvalues at its
parameter point and integrates to one. The Fig. 4 display range and the
Fig. 5(a) disorder selections follow the published panels.
