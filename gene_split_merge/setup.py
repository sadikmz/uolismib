#!/usr/bin/env python3
"""
Setup script for Gene Split/Merge Detection Tool
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "docs" / "usage_readme.md"
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = "A high-performance tool for detecting gene split and merge events between genome annotations using DIAMOND BLASTP."

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
    author="ISMIB",
    author_email="",
    description="Detect gene split and merge events between genome annotations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/gene-split-merge",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "biopython>=1.79",
        "pandas>=1.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "gene-split-merge=gene_split_merge.core:main",
            "gene-clustering=gene_split_merge.cli_clustering:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="bioinformatics genomics annotation gene-structure",
    project_urls={
        "Documentation": "https://github.com/yourusername/gene-split-merge/docs",
        "Source": "https://github.com/yourusername/gene-split-merge",
        "Tracker": "https://github.com/yourusername/gene-split-merge/issues",
    },
)
