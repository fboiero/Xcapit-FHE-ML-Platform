#!/usr/bin/env python3
"""Xcapit FHE-ML SDK Command Line Interface.

This module is a wrapper for backward compatibility.
The actual implementation is in the sdk/cli/ package.

Usage:
    xcapit-fhe init -o ./workspace
    xcapit-fhe encrypt --input data.csv --output encrypted.bin --target price
    xcapit-fhe train --model linear-regression --data encrypted.bin --output model.bin
    xcapit-fhe predict --model model.bin --input encrypted.bin
    xcapit-fhe decrypt --input encrypted.bin --output decrypted.csv
"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
