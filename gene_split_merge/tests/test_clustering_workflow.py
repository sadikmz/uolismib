#!/usr/bin/env python3
"""
Test Clustering Workflow
=========================
Test the run_clustering.py script with synthetic data.
"""

import tempfile
import os
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord


def create_test_data():
    """Create test protein files."""
    print("Creating test data...")

    # Create reference proteins (5 sequences)
    ref_proteins = []
    for i in range(1, 6):
        seq = "M" + "ACDEFGHIKLMNPQRSTVWY" * 20
        record = SeqRecord(
            Seq(seq),
            id=f"GENE_{i:03d}",  # Same IDs in both files (intentional)
            description=f"Reference protein {i}"
        )
        ref_proteins.append(record)

    # Create query proteins (5 sequences, same IDs!)
    qry_proteins = []
    for i in range(1, 6):
        # Slightly different sequences
        seq = "M" + "ACDEFGHIKLMNPQRSTVWY" * 20
        seq = seq[:100] + "A" + seq[101:]  # Minor change
        record = SeqRecord(
            Seq(seq),
            id=f"GENE_{i:03d}",  # Same IDs as reference (will be renamed)
            description=f"Query protein {i}"
        )
        qry_proteins.append(record)

    # Add some duplicates for clustering demo
    for i in [1, 2]:
        seq = str(ref_proteins[i-1].seq)
        for copy_num in range(1, 3):
            record = SeqRecord(
                Seq(seq),
                id=f"GENE_{i:03d}_DUP{copy_num}",
                description=f"Reference protein {i} duplicate {copy_num}"
            )
            ref_proteins.append(record)

    # Write to temp files
    tmpdir = tempfile.mkdtemp(prefix="cluster_test_")
    ref_file = os.path.join(tmpdir, "ref_proteins.fasta")
    qry_file = os.path.join(tmpdir, "qry_proteins.fasta")

    SeqIO.write(ref_proteins, ref_file, "fasta")
    SeqIO.write(qry_proteins, qry_file, "fasta")

    print(f"Created test data in: {tmpdir}")
    print(f"  Reference proteins: {len(ref_proteins)} sequences")
    print(f"  Query proteins: {len(qry_proteins)} sequences")
    print(f"  Note: IDs GENE_001-005 appear in BOTH files (will be renamed with _REF/_QRY)")

    return ref_file, qry_file, tmpdir


def test_combined_database():
    """Test the combined database functionality."""
    print("\n" + "="*60)
    print("TEST: Combined Database with ID Renaming")
    print("="*60)

    ref_file, qry_file, tmpdir = create_test_data()
    output_file = os.path.join(tmpdir, "combined_clusters.tsv")

    print("\nTest command:")
    print(f"""
python3 run_clustering.py \\
    --workflow linclust \\
    --database all \\
    --ref-proteins {ref_file} \\
    --qry-proteins {qry_file} \\
    --output {output_file} \\
    --params "--approx-id 95 --member-cover 80" \\
    --threads 4
    """)

    print("\nExpected behavior:")
    print("1. IDs will be renamed:")
    print("   GENE_001 (ref) -> GENE_001_REF")
    print("   GENE_001 (qry) -> GENE_001_QRY")
    print("2. Duplicates will cluster together:")
    print("   GENE_001_REF, GENE_001_DUP1_REF, GENE_001_DUP2_REF -> 1 cluster")
    print("3. Ref and query versions will be in separate clusters (different sequences)")

    print("\nTo run this test manually:")
    print(f"cd {os.path.dirname(ref_file)}")
    print("Then run the command above")

    print(f"\nTest data location: {tmpdir}")
    print("(Temporary directory - will be cleaned up manually)")


def main():
    """Run tests."""
    print("\n" + "="*60)
    print("CLUSTERING WORKFLOW TEST SUITE")
    print("="*60)

    test_combined_database()

    print("\n" + "="*60)
    print("TEST PREPARATION COMPLETE")
    print("="*60)
    print("\nThe test data has been created.")
    print("Run the commands above to test the clustering workflow manually.")
    print("\nKey features to verify:")
    print("✓ ID renaming (_REF and _QRY suffixes)")
    print("✓ Parameter parsing from comma-separated string")
    print("✓ Clustering of combined database")
    print("✓ Proper handling of duplicate IDs across files")


if __name__ == '__main__':
    main()
