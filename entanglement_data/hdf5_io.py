"""Output handling shared by the generators."""

from contextlib import contextmanager
from datetime import datetime, timezone
import os
from pathlib import Path
import tempfile

import h5py
import numpy as np

from . import __version__


def lattice_size(value):
    value = int(value)
    if value < 2 or value % 2:
        raise ValueError("L must be even and at least 2 for the half-space cut")
    return value


@contextmanager
def new_h5(path):
    """Publish a complete file atomically; never overwrite an existing output."""
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"Output already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".partial",
                                     dir=path.parent)
    os.close(fd)
    try:
        with h5py.File(temporary, "w") as handle:
            yield handle
        # A hard link also refuses a destination created by another process.
        os.link(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def model_attributes(handle, size, generator):
    handle.attrs.update({
        "L": size,
        "t": 1.0,
        "t_0": 1.0,
        "t_z": -1.0,
        "obc_x": False,
        "obc_y": False,
        "obc_z": False,
        "filling": 0.5,
        "subsystem": "x < L/2, both orbitals",
        "generator": generator,
        "generator_version": __version__,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "numpy_version": np.__version__,
        "h5py_version": h5py.__version__,
    })
