#!/usr/bin/env python3
"""Main entry point for the jcleasing package."""

import sys
import os

# Add src directory to Python path
src_dir = os.path.join(os.path.dirname(__file__), "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
 
from jcleasing.cli import main # noqa: E402

if __name__ == "__main__":
    main()
