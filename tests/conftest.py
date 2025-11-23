"""Shared pytest configuration and fixtures"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path so we can import pavprot
sys.path.insert(0, str(Path(__file__).parent.parent))
