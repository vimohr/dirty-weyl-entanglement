#!/usr/bin/env python3
"""Extract W=0 and W=2 at m_z=0 from a half-filling disorder sweep."""

import argparse

from entanglement_data.extract import extract


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="data/half_filling_data_20260519_134201.h5")
    parser.add_argument("--output", default="data/entanglement_spectrum_1c.h5")
    parser.add_argument("--realization", type=int, default=0)
    args = parser.parse_args()
    try:
        output = extract(args.source, args.output, args.realization)
    except (ValueError, OSError) as error:
        parser.exit(1, f"{error}\n")
    print(f"Written {output}")


if __name__ == "__main__":
    main()
