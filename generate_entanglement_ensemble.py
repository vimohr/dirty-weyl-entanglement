#!/usr/bin/env python3
"""Generate a half-filling ensemble with the archived disorder or mass grid."""

import argparse

from entanglement_data.entanglement_ensemble import generate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset", required=True, choices=["w-sweep", "m-sweep"])
    parser.add_argument("--size", type=int, default=10, help="Even cubic lattice size (10)")
    parser.add_argument("--samples", type=int, default=10000, help="Realizations (10000)")
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--threads", type=int, default=1, help="OpenMP worker threads (1)")
    parser.add_argument("--batch-size", type=int, default=8, help="Realizations per write (8)")
    parser.add_argument("--rng", choices=["task", "legacy-thread"], default="task",
                        help="task is independent of scheduling; legacy-thread follows the old RNG policy")
    parser.add_argument("--backend", help="Path to the compiled shared library")
    parser.add_argument("--output", help="Default: data/disorder_entanglement_ensemble.h5 or data/mass_entanglement_ensemble.h5")
    args = parser.parse_args()
    try:
        output = generate(args.preset, args.output, args.size, args.samples,
                          args.seed, args.threads, args.batch_size, args.rng, args.backend)
    except (ValueError, OSError, RuntimeError) as error:
        parser.exit(1, f"{error}\n")
    print(f"Written {output}")


if __name__ == "__main__":
    main()
