"""Configure pytest for the Azul package tests."""

import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, src_dir)
