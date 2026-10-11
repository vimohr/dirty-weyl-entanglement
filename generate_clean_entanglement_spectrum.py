#!/usr/bin/env python3
"""Generate the clean momentum-resolved entanglement spectrum in the original HDF5 layout."""

import argparse

from entanglement_data.clean_spectrum import generate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, default=60, help="Even cubic lattice size (60)")
    parser.add_argument("--mass", type=float, default=0.0, help="m_z (0)")
    parser.add_argument("--output", default="data/clean_entanglement_spectrum.h5")
    args = parser.parse_args()
    try:
        output = generate(args.size, args.mass, args.output)
    except (ValueError, OSError) as error:
        parser.exit(1, f"{error}\n")
    print(f"Written {output}")


if __name__ == "__main__":
    main()
