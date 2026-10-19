"""Shared paths for source and PyInstaller distributions."""
from pathlib import Path
import sys

RESOURCE_ROOT = Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent.parent
