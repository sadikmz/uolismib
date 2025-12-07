#!/usr/bin/env python3
"""
Setup script for Gene Split/Merge Detection Tool
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = "A simple Python implementation for detecting gene split and merge events between genome annotations using DIAMOND BLASTP."

# Read version from __init__.py
version = {}
with open("src/gene_split_merge/__init__.py") as f:
    for line in f:
        if line.startswith("__version__"):
            exec(line, version)
            break

setup(
    name="gene-split-merge",
    version=version.get("__version__", "1.5.0"),
    author="Sadik M",
    description="Detect gene split and merge events between genome annotations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.7",
    install_requires=[
        "biopython>=1.79",
        "pandas>=1.3.0",
    ],
    entry_points={
        "console_scripts": [
            "gene-split-merge=gene_split_merge.core:main",
            "gene-clustering=gene_split_merge.cli_clustering:main",
        ],
    },
    include_package_data=True,
)
