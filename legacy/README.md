# Historical source snapshots

These seven files document the origins of the four archived datasets and the
supported C++ backend. They were copied from the parent research workspace
without editing their contents. Use the top-level generators for new calculations.

| File | Purpose |
| --- | --- |
| `quickie.py` | Contains the original L=60 clean 1b calculation; generation and writing are currently disabled. |
| `quick_plot.py` | Reads the original disorder ensemble and writes the two-spectrum 1c extract and plots. |
| `run_half_filling_cdb8984.py` | Older wrapper whose HDF5 format matches the original disorder sweep; its saved parameter grid differs from that run. |
| `run_half_filling_cdf3307.py` | Git snapshot with the original 41-point W=2 mass grid and 10,000 realizations. |
| `testvi_cpp_current.cpp` | Working-tree C++ calculation used as the basis of the supported backend. |
| `testvi_cpp_cdb8984.cpp` | Older fixed-mass C++ snapshot. |
| `testvi_cpp_cdf3307.cpp` | C++ snapshot corresponding to the saved mass-sweep wrapper. |

The old wrappers expect different C++ signatures and a library next to the
script. Do not pair these historical wrappers with the new backend.
Exploratory notebooks and the later experimental wrapper are omitted because
their saved runs do not describe these four datasets. Earlier Git revisions
retain those snapshots.
See [provenance](../docs/PROVENANCE.md) for the known gaps in execution history.
