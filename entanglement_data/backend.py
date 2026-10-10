"""ctypes interface to the included Eigen/OpenMP half-filling kernel."""

import ctypes
from pathlib import Path

import numpy as np

from .io import lattice_size

ROOT = Path(__file__).resolve().parent.parent


def default_library():
    for name in ("libentanglement_backend.so", "libentanglement_backend.dylib",
                 "entanglement_backend.dll"):
        path = ROOT / "build" / name
        if path.exists():
            return path
    raise FileNotFoundError(
        "Build the C++ backend first: cmake -S . -B build -DCMAKE_BUILD_TYPE=Release "
        "then cmake --build build --parallel 2"
    )


class Model:
    def __init__(self, size, library=None):
        self.size = lattice_size(size)
        library = Path(library) if library is not None else default_library()
        self.lib = ctypes.CDLL(str(library.resolve()))
        self.lib.spectrum_backend_api.restype = ctypes.c_int
        if self.lib.spectrum_backend_api() != 1:
            raise RuntimeError("The backend API version is incompatible")
        self.lib.spectrum_last_error.restype = ctypes.c_char_p
        self.lib.spectrum_create_model.argtypes = [ctypes.c_int]
        self.lib.spectrum_create_model.restype = ctypes.c_void_p
        self.lib.spectrum_destroy_model.argtypes = [ctypes.c_void_p]
        self.lib.spectrum_destroy_model.restype = None
        pointer = ctypes.POINTER(ctypes.c_double)
        self.lib.spectrum_compute_batch.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_int, pointer, pointer, ctypes.c_int,
            ctypes.c_uint64, ctypes.c_int, ctypes.c_int, pointer, pointer,
        ]
        self.lib.spectrum_compute_batch.restype = ctypes.c_int
        self.pointer = self.lib.spectrum_create_model(self.size)
        if not self.pointer:
            raise RuntimeError(self._error())

    def _error(self):
        return self.lib.spectrum_last_error().decode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        if self.pointer:
            self.lib.spectrum_destroy_model(self.pointer)
            self.pointer = None

    def compute(self, disorders, masses, first=0, count=1, seed=1337,
                threads=1, rng="task"):
        if not self.pointer:
            raise RuntimeError("The model has been closed")
        w = np.ascontiguousarray(disorders, dtype=np.float64)
        m = np.ascontiguousarray(masses, dtype=np.float64)
        if w.ndim != 1 or w.size == 0 or m.shape != w.shape:
            raise ValueError("Disorder and mass must be nonempty one-dimensional arrays of equal shape")
        if not np.all(np.isfinite(w)) or not np.all(np.isfinite(m)) or np.any(w < 0):
            raise ValueError("Parameters must be finite and W must be nonnegative")
        if first < 0 or count < 1 or threads < 1 or first + count >= 2**31:
            raise ValueError("Invalid realization range or thread count")
        if count * w.size >= 2**31:
            raise ValueError("The batch has too many parameter tasks")
        if not 0 <= seed < 2**64 or rng not in ("task", "legacy-thread"):
            raise ValueError("Seed must be a uint64 and RNG must be task or legacy-thread")
        entropy = np.empty((count, len(w)), dtype=np.float64)
        occupations = np.empty((count, len(w), self.size**3), dtype=np.float64)
        pointer = ctypes.POINTER(ctypes.c_double)
        status = self.lib.spectrum_compute_batch(
            self.pointer, first, count, w.ctypes.data_as(pointer), m.ctypes.data_as(pointer),
            len(w), seed, rng == "legacy-thread", threads,
            entropy.ctypes.data_as(pointer), occupations.ctypes.data_as(pointer),
        )
        if status:
            raise RuntimeError(self._error())
        return entropy, occupations
