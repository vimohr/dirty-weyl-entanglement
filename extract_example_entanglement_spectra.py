#!/usr/bin/env python3
"""Extract example entanglement spectra at W=0 and W=2, m_z=0 from a disorder sweep."""

import argparse

from entanglement_data.example_spectra import extract


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="data/disorder_entanglement_ensemble.h5")
    parser.add_argument("--output", default="data/example_entanglement_spectra.h5")
    parser.add_argument("--realization", type=int, default=0)
    args = parser.parse_args()
    try:
        output = extract(args.source, args.output, args.realization)
    except (ValueError, OSError) as error:
        parser.exit(1, f"{error}\n")
    print(f"Written {output}")


if __name__ == "__main__":
    main()
