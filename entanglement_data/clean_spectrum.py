"""The transverse-momentum decomposition used in the original 1b calculation."""

import numpy as np

from .hdf5_io import lattice_size, model_attributes, new_h5

SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.diag([1, -1]).astype(complex)


def dft(size):
    indices = np.arange(size)
    return np.exp(-2j * np.pi * np.outer(indices, indices) / size) / np.sqrt(size)


def block_spectrum(size, iy, iz, mass=0.0, transform=None):
    """Return L occupations at fixed ky=2*pi*iy/L, kz=2*pi*iz/L."""
    size = lattice_size(size)
    if not 0 <= iy < size or not 0 <= iz < size:
        raise ValueError("Momentum indices must be between 0 and L-1")
    if not np.isfinite(mass):
        raise ValueError("Mass must be finite")
    if transform is None:
        transform = np.kron(dft(size), np.eye(2))
    kx = 2 * np.pi * np.arange(size) / size
    ky, kz = 2 * np.pi * np.array([iy, iz]) / size
    momentum_h = np.zeros((2 * size, 2 * size), dtype=complex)
    for ix, k in enumerate(kx):
        block = (np.sin(k) * SX + np.sin(ky) * SY
                 + (-np.cos(kz) - mass + (2 - np.cos(k) - np.cos(ky))) * SZ)
        momentum_h[2 * ix:2 * ix + 2, 2 * ix:2 * ix + 2] = block
    real_h = transform.conj().T @ momentum_h @ transform
    _, vectors = np.linalg.eigh(real_h)
    # Fill exactly half the orbitals, including the legacy choice at zero modes.
    restricted = vectors[:size, :size]
    # Follow historical_sources/clean_spectrum_calculation.py; eigenvalues are real.
    correlation = restricted.conj() @ restricted.T
    return np.linalg.eigvalsh(correlation)


def generate(size=60, mass=0.0, output="data/clean_entanglement_spectrum.h5"):
    size = lattice_size(size)
    if not np.isfinite(mass):
        raise ValueError("Mass must be finite")
    transform = np.kron(dft(size), np.eye(2))
    with new_h5(output) as handle:
        spectrum = handle.create_dataset("eigvals", shape=(size * size, size),
                                         dtype="f8")
        for iz in range(size):
            for iy in range(size):
                spectrum[iy + size * iz] = block_spectrum(size, iy, iz, mass, transform)
            print(f"kz blocks complete: {iz + 1}/{size}", flush=True)
        model_attributes(handle, size, "generate_clean_entanglement_spectrum.py")
        handle.attrs["m_z"] = mass
        handle.attrs["axis_order"] = "row = iy + L*iz; columns = sorted occupations"
    return output
