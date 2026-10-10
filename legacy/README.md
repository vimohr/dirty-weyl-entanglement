# Preserved source snapshots

These files were copied from the parent research workspace and are retained as
provenance. Their contents have not been edited. Use the top-level supported
generators for new calculations.

| File | Purpose |
| --- | --- |
| `quickie.py` | Contains the original L=60 clean 1b calculation; generation and writing are currently disabled. |
| `testvi.ipynb` | Experimental notebook that also writes the 1b filename with a different saved lattice. |
| `quick_plot.py` | Reads the original disorder ensemble and writes the two-spectrum 1c extract and plots. |
| `quick_check.ipynb` | An alternative 1c writer whose saved input now points at a different dataset. |
| `run_half_filling.py` | Working-tree wrapper from the parent, including later lattice-size and parameter changes. |
| `run_half_filling_cdb8984.py` | Older wrapper whose HDF5 format matches the original disorder sweep; its saved parameter grid differs from that run. |
| `run_half_filling_cdf3307.py` | Git snapshot with the original 41-point W=2 mass grid and 10,000 realizations. |
| `testvi_cpp_current.cpp` | Working-tree C++ calculation used as the basis of the supported backend. |
| `testvi_cpp_cdb8984.cpp` | Older fixed-mass C++ snapshot. |
| `testvi_cpp_cdf3307.cpp` | C++ snapshot corresponding to the saved mass-sweep wrapper. |

The old wrappers expect different C++ signatures and a library next to the
script. Do not pair these historical wrappers with the new backend.
The notebooks retain their saved outputs as historical evidence.
See [provenance](../docs/PROVENANCE.md) for the known gaps in execution history.
