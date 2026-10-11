#!/usr/bin/env python3
"""Generate figure plots and numerical tables from the archived data.

These are new plotting routines, not the authors' original plotting code.
EDOS bin counts are configurable reconstruction choices.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import h5py
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ORDERS = np.array([1, 2, 3, 10, 20, 30, 40, 50])


def checked_xi(values):
    values = np.asarray(values, dtype=float)
    if not np.all(np.isfinite(values)):
        raise ValueError("Nonfinite correlation eigenvalues")
    if np.any((values < -1e-10) | (values > 1 + 1e-10)):
        raise ValueError("Correlation eigenvalues exceed numerical endpoint tolerance")
    return np.clip(values, 0.0, 1.0)


def entropy(x, order):
    """Entropy in nats, with the mathematical endpoint limit at xi=0 and 1."""
    if order == 1:
        terms = np.zeros_like(x)
        mask = x > 0
        terms[mask] = -x[mask] * np.log(x[mask])
        y = 1 - x
        mask = y > 0
        terms[mask] -= y[mask] * np.log(y[mask])
        return terms.sum(axis=-1)
    return np.log(x ** order + (1 - x) ** order).sum(axis=-1) / (1 - order)


def save_csv(path, header, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def save_plot(fig, out, name):
    fig.savefig(out / f"{name}.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def figure1b(root, out):
    with h5py.File(root / "entanglement_spectrum_1b.h5", "r") as f:
        x = checked_xi(f["eigvals"][:])
    if x.shape != (3600, 60):
        raise ValueError("Expected eigvals shape (3600,60), ky varying fastest")
    # Flat row = kz_index*60 + ky_index, established from half modes and PDF markers.
    x = x.reshape(60, 60, 60)
    k = 2 * np.pi * np.fft.fftshift(np.fft.fftfreq(60))
    x = np.fft.fftshift(x, axes=0)
    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.plot(np.repeat(k, 60 * 60), x.reshape(-1), ".", ms=0.6)
    ax.set(xlabel=r"$k_z$", ylabel=r"$\xi$", ylim=(-0.02, 1.02))
    ax.set_xticks([-np.pi, 0, np.pi], [r"$-\pi$", "0", r"$\pi$"])
    ax.set_yticks([0, 0.5, 1], ["0", "1/2", "1"])
    save_plot(fig, out, "figure1b")


def figure1c(root, out):
    # Both standalone spectra match the published source spectra exactly.
    with h5py.File(root / "entanglement_spectrum_1c.h5", "r") as f:
        w = f["w_array"][:]
        index = np.flatnonzero(np.isclose(w, 2.0))
        if len(index) != 1:
            raise ValueError("Expected one W=2 point")
        clean = checked_xi(f["eigvals"][0, :])
        dirty = checked_xi(f["eigvals"][int(index[0]), :])
    n = np.arange(485, 516)  # Zero-based labels agree with the PDF marker positions.
    fig, ax = plt.subplots(figsize=(5, 2.8))
    ax.plot(n, clean[n], ".", label="clean WSM")
    ax.plot(n, dirty[n], ".", label="W=2.0")
    ax.set(xlabel=r"$n$", ylabel=r"$\xi$")
    ax.legend()
    save_plot(fig, out, "figure1c")
    save_csv(out / "figure1c.csv", ["n_zero_based", "xi_W0", "xi_W2_realization0"],
             zip(n, clean[n], dirty[n]))


def edos(root, out, filename, parameter, targets, bins, name, batch_size):
    edges = np.linspace(0, 1, bins + 1)
    counts = np.zeros((len(targets), bins), dtype=np.int64)
    with h5py.File(root / filename, "r") as f:
        axis = f[parameter][:]
        indices = []
        for target in targets:
            found = np.flatnonzero(np.isclose(axis, target))
            if len(found) != 1:
                raise ValueError(f"Parameter {target} missing or duplicated")
            indices.append(int(found[0]))
        nr, _, na = f["eigvals"].shape
        for first in range(0, nr, batch_size):
            # Read all controls in a batch to avoid repeatedly decompressing chunks.
            raw = f["eigvals"][first:first + batch_size, :, :]
            for j, index in enumerate(indices):
                counts[j] += np.histogram(checked_xi(raw[:, index, :]), edges)[0]
        density = counts / (nr * na * np.diff(edges)[None, :])
    if not np.all(counts.sum(axis=1) == nr * na):
        raise ValueError("Histogram does not retain every eigenvalue")
    fig, axes = plt.subplots(1, len(targets), figsize=(12, 2.7), sharey=True)
    for j, (ax, target) in enumerate(zip(axes, targets)):
        ax.stairs(density[j], edges, fill=True, color="0.65")
        ax.set_yscale("log")
        ax.set(xlim=(0, 1), ylim=((1e-3, 100) if name == "figure2" else (1e-9, 100)),
               title=f"{'W' if parameter == 'w_array' else 'm'}={target:g}")
        ax.set_xticks([0, 0.5, 1], ["0", "1/2", "1"])
    axes[0].set_ylabel(r"$\nu_S$")
    fig.supxlabel(r"$\xi$")
    fig.tight_layout()
    save_plot(fig, out, name)
    rows = ((target, edges[i], edges[i + 1], int(counts[j, i]), density[j, i])
            for j, target in enumerate(targets) for i in range(bins))
    save_csv(out / f"{name}_histograms.csv", ["parameter", "xi_left", "xi_right", "count", "density"], rows)


def entropy_figures(root, out, requested, batch_size):
    with h5py.File(root / "half_filling_data_w_sweep_10000.h5", "r") as f:
        w = f["w_array"][:]
        nr, nw, _ = f["eigvals"].shape
        samples = np.empty((nr, nw, len(ORDERS)))
        for first in range(0, nr, batch_size):
            x = checked_xi(f["eigvals"][first:first + batch_size, :, :])
            for j, order in enumerate(ORDERS):
                samples[first:first + len(x), :, j] = entropy(x, int(order))
            if first % (8 * batch_size) == 0:
                print(f"Entropy reconstruction: {first + len(x)}/{nr} realizations", flush=True)
    means = samples.mean(axis=0)
    variances = samples.var(axis=0, ddof=0)
    del samples
    delta = means[1:] - means[0]
    with np.errstate(invalid="ignore", divide="ignore"):
        logs = np.where(delta > 0, np.log(delta), np.nan)
    alpha = np.gradient(logs, np.log(w[1:]), axis=0)
    rows = ((w[i], int(order), means[i, j], variances[i, j],
             np.sqrt(variances[i, j] / nr), "" if i == 0 or not np.isfinite(alpha[i - 1, j]) else alpha[i - 1, j])
            for i in range(nw) for j, order in enumerate(ORDERS))
    save_csv(out / "entropy_statistics.csv",
             ["W", "renyi_order", "mean_nats", "population_variance_nats_squared", "standard_error_nats", "alpha"], rows)
    for name, js, xmax in [("3", [0, 1, 2], 8), ("6", [3, 4, 5, 6, 7], 7)]:
        if name not in requested:
            continue
        fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
        for j in js:
            line, = axes[0].plot(w, means[:, j], label=f"S{ORDERS[j]}")
            if name == "3":
                # Mean +/- population variance matches the PDF's shaded bands.
                axes[0].fill_between(w, means[:, j] - variances[:, j],
                                     means[:, j] + variances[:, j], color=line.get_color(), alpha=0.2)
            axes[1].plot(w[1:], alpha[:, j], label=f"alpha{ORDERS[j]}")
        for ax in axes:
            ax.set(xlabel=r"$W/t$", xlim=(0, xmax))
            ax.legend(fontsize=8)
            if name == "3":
                ax.axvspan(3.65, 3.85, color="0.6", alpha=0.35)
        axes[0].set_ylabel("Entropy (nats)")
        axes[1].set_ylabel(r"$\alpha_i$")
        axes[1].set_xlim(0, 6 if name == "3" else 7)
        axes[1].set_ylim((-1.5, 3.3) if name == "3" else (-5.5, 7.5))
        fig.tight_layout()
        save_plot(fig, out, f"figure{name}")


def figure5(root, out):
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.3))
    selections = [(0, [1, 2, 3, 3.3, 3.5, 3.7, 3.8, 3.9, 4, 4.1]),
                  ([0, -0.6, -0.7, -0.8, -0.9], 2),
                  ([-1, -1.1, -1.2, -1.3, -1.4, -1.5, -1.6], 2)]
    rows = []
    for panel, (masses, disorders) in enumerate(selections):
        pairs = [(masses, w) for w in disorders] if panel == 0 else [(m, disorders) for m in masses]
        for m, w in pairs:
            name = f"dos_m{m:.1f}_W{w:.1f}.dat"
            # Preserve small negative KPM values; do not silently alter source tables.
            data = np.loadtxt(root / "DoS_data" / name)
            axes[panel].plot(data[:, 0], data[:, 1], label=f"{'W' if panel == 0 else 'm'}={w if panel == 0 else m:g}")
            rows.extend((panel, m, w, float(e), float(dos)) for e, dos in data)
        axes[panel].set(xlabel=r"$E/t$", xlim=((-0.7, 0.7) if panel == 0 else ((-0.45, 0.45) if panel == 1 else (-0.8, 0.8))),
                        ylim=((0, 0.11) if panel == 0 else ((0, 0.021) if panel == 1 else (0, 0.035))))
        axes[panel].set_ylabel(r"$\nu_A$")
        axes[panel].legend(fontsize=6)
    fig.tight_layout()
    save_plot(fig, out, "figure5")
    save_csv(out / "figure5_dos.csv", ["panel_zero_based", "m", "W", "E", "average_DOS"], rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--figures", nargs="+", choices=["1b", "1c", "2", "3", "4", "5", "6"],
                        default=["1b", "1c", "2", "3", "4", "5", "6"])
    parser.add_argument("--batch-size", type=int, default=313)
    parser.add_argument("--bins2", type=int, default=119,
                        help="EDOS bin count for figure 2; inferred bar spacing, exact original recipe unconfirmed")
    parser.add_argument("--bins4", type=int, default=100,
                        help="EDOS bin count for figure 4; illustrative, exact original recipe unconfirmed")
    args = parser.parse_args()
    if min(args.batch_size, args.bins2, args.bins4) < 1:
        parser.error("Batch size and bin counts must be positive")
    out = args.output or args.root / "reconstructed_figures"
    out.mkdir(parents=True, exist_ok=True)
    if "1b" in args.figures:
        figure1b(args.root, out)
    if "1c" in args.figures:
        figure1c(args.root, out)
    if "2" in args.figures:
        edos(args.root, out, "half_filling_data_w_sweep_10000.h5", "w_array",
             [1, 2, 3, 3.8, 4.4], args.bins2, "figure2", args.batch_size)
    if "4" in args.figures:
        edos(args.root, out, "half_filling_data_m_sweep_10000.h5", "mz_array",
             [0, -0.6, -1.1, -1.2, -1.6], args.bins4, "figure4", args.batch_size)
    if "5" in args.figures:
        figure5(args.root, out)
    if {"3", "6"} & set(args.figures):
        entropy_figures(args.root, out, args.figures, args.batch_size)
    print(f"Saved reconstructions and tables in {out}")


if __name__ == "__main__":
    main()
