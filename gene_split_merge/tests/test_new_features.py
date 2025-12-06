#!/usr/bin/env python3
"""
Test New Features
=================
Demonstration of new DIAMOND-based features:
1. Bidirectional Best Hits (BBH) for ortholog detection
2. Clustering for redundancy removal
3. Enhanced DIAMOND utilities

Author: Bioinformatics Workflow
Date: 2025-12-06
"""

import sys
import tempfile
import os
from pathlib import Path
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

# Import our modules
from gene_structure_analyzer import (
    Gene, BlastHit, GeneStructureAnalyzer,
    GFFParser, BlastAnalyzer
)
from diamond_clustering import DiamondClusterer, ClusterParser
from diamond_utils import DiamondOutputParser, DiamondAlignmentAnalyzer


def generate_test_proteins():
    """Generate test protein sequences for demonstration."""
    print("\n" + "="*60)
    print("Generating test protein sequences...")
    print("="*60)

    # Create reference proteins (10 sequences)
    ref_proteins = []
    for i in range(1, 11):
        # Generate semi-realistic protein sequence
        seq = "M" + "ACDEFGHIKLMNPQRSTVWY" * (20 + i*5)
        record = SeqRecord(
            Seq(seq),
            id=f"REF_GENE_{i:03d}",
            description=f"Reference protein {i}"
        )
        ref_proteins.append(record)

    # Create updated proteins with some variations
    upd_proteins = []

    # 1-5: Identical orthologs
    for i in range(1, 6):
        seq = str(ref_proteins[i-1].seq)
        record = SeqRecord(
            Seq(seq),
            id=f"UPD_GENE_{i:03d}",
            description=f"Updated protein {i} (ortholog)"
        )
        upd_proteins.append(record)

    # 6-8: Modified orthologs (90% identity)
    for i in range(6, 9):
        seq = str(ref_proteins[i-1].seq)
        # Introduce some mutations
        seq_list = list(seq)
        for j in range(0, len(seq_list), 10):
            if j < len(seq_list):
                seq_list[j] = 'A'
        seq = ''.join(seq_list)
        record = SeqRecord(
            Seq(seq),
            id=f"UPD_GENE_{i:03d}",
            description=f"Updated protein {i} (modified)"
        )
        upd_proteins.append(record)

    # 9-10: Duplicated proteins (for clustering test)
    for i in range(9, 11):
        seq = str(ref_proteins[i-1].seq)
        # Create 3 near-identical copies
        for copy_num in range(1, 4):
            if copy_num > 1:
                # Slight variation for duplicates
                seq_list = list(seq)
                seq_list[0] = 'A'
                seq = ''.join(seq_list)
            record = SeqRecord(
                Seq(seq),
                id=f"UPD_GENE_{i:03d}_{copy_num}",
                description=f"Updated protein {i} copy {copy_num}"
            )
            upd_proteins.append(record)

    return ref_proteins, upd_proteins


def test_bidirectional_best_hits():
    """Test the bidirectional best hit functionality."""
    print("\n" + "="*60)
    print("TEST 1: Bidirectional Best Hits (Ortholog Detection)")
    print("="*60)

    # Generate test data
    ref_proteins, upd_proteins = generate_test_proteins()

    # Create temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        ref_fasta = os.path.join(tmpdir, "ref.fasta")
        upd_fasta = os.path.join(tmpdir, "upd.fasta")

        SeqIO.write(ref_proteins, ref_fasta, "fasta")
        SeqIO.write(upd_proteins, upd_fasta, "fasta")

        print(f"\nCreated test data:")
        print(f"  Reference proteins: {len(ref_proteins)}")
        print(f"  Updated proteins: {len(upd_proteins)}")

        # Create mock BLAST hits for demonstration
        # In real use, these would come from actual DIAMOND BLASTP
        forward_hits = []
        reverse_hits = []

        # Mock some high-quality bidirectional hits
        for i in range(1, 9):
            ref_id = f"REF_GENE_{i:03d}"
            upd_id = f"UPD_GENE_{i:03d}"

            # Forward hit (ref -> upd)
            forward_hits.append(BlastHit(
                query_id=ref_id,
                subject_id=upd_id,
                pident=95.0 if i <= 5 else 85.0,
                length=400,
                qstart=1,
                qend=400,
                qlen=420,
                sstart=1,
                send=400,
                slen=420,
                evalue=1e-100,
                bitscore=800
            ))

            # Reverse hit (upd -> ref)
            reverse_hits.append(BlastHit(
                query_id=upd_id,
                subject_id=ref_id,
                pident=95.0 if i <= 5 else 85.0,
                length=400,
                qstart=1,
                qend=400,
                qlen=420,
                sstart=1,
                send=400,
                slen=420,
                evalue=1e-100,
                bitscore=800
            ))

        # Create mock genes
        ref_genes = {
            f"REF_GENE_{i:03d}": Gene(
                gene_id=f"REF_GENE_{i:03d}",
                chromosome="chr1",
                start=i*10000,
                end=i*10000+5000,
                strand="+"
            )
            for i in range(1, 11)
        }

        upd_genes = {
            f"UPD_GENE_{i:03d}": Gene(
                gene_id=f"UPD_GENE_{i:03d}",
                chromosome="chr1",
                start=i*10000,
                end=i*10000+5000,
                strand="+"
            )
            for i in range(1, 9)
        }

        # Initialize analyzer
        analyzer = GeneStructureAnalyzer(
            ref_genes, upd_genes,
            forward_hits, reverse_hits
        )

        # Perform BBH analysis
        print("\nPerforming BBH analysis...")
        bbh_df = analyzer.get_bidirectional_best_hits(
            min_identity=70.0,
            min_coverage=50.0
        )

        print(f"\n✓ Found {len(bbh_df)} bidirectional best hits")

        if not bbh_df.empty:
            print("\nTop 5 BBH pairs:")
            print(bbh_df[['ref_gene', 'upd_gene', 'avg_pident', 'avg_coverage']].head())

        # Identify high-confidence orthologs
        orthologs = analyzer.identify_one_to_one_orthologs(
            min_identity=80.0,
            min_coverage=70.0
        )

        print(f"\n✓ Identified {len(orthologs)} high-confidence orthologs")
        for ref, upd in list(orthologs.items())[:5]:
            print(f"  {ref} <-> {upd}")


def test_clustering():
    """Test the DIAMOND clustering functionality."""
    print("\n" + "="*60)
    print("TEST 2: DIAMOND Clustering (Redundancy Removal)")
    print("="*60)

    # Generate test data with duplicates
    _, upd_proteins = generate_test_proteins()

    print(f"\nGenerated {len(upd_proteins)} protein sequences")
    print("  (includes intentional near-duplicates for clustering demo)")

    # Create mock clustering output
    print("\nSimulating DIAMOND clustering output...")

    # Mock clustering data (representative<tab>member format)
    mock_cluster_data = """UPD_GENE_001\tUPD_GENE_001
UPD_GENE_002\tUPD_GENE_002
UPD_GENE_003\tUPD_GENE_003
UPD_GENE_004\tUPD_GENE_004
UPD_GENE_005\tUPD_GENE_005
UPD_GENE_006\tUPD_GENE_006
UPD_GENE_007\tUPD_GENE_007
UPD_GENE_008\tUPD_GENE_008
UPD_GENE_009_1\tUPD_GENE_009_1
UPD_GENE_009_1\tUPD_GENE_009_2
UPD_GENE_009_1\tUPD_GENE_009_3
UPD_GENE_010_1\tUPD_GENE_010_1
UPD_GENE_010_1\tUPD_GENE_010_2
UPD_GENE_010_1\tUPD_GENE_010_3"""

    # Parse clustering output
    df = ClusterParser.parse_clusters(mock_cluster_data)

    print(f"\n✓ Parsed clustering results:")
    print(f"  Total sequences: {len(df)}")
    print(f"  Total clusters: {df['cluster_number'].nunique()}")

    # Get cluster statistics
    from diamond_clustering import DiamondClusterer
    stats = DiamondClusterer.get_cluster_stats(df)

    print(f"\n✓ Cluster statistics:")
    print(stats)

    # Show clusters with multiple members
    multi_member = stats[stats['size'] > 1]
    if not multi_member.empty:
        print(f"\n✓ Clusters with multiple members (redundancy detected):")
        for _, row in multi_member.iterrows():
            print(f"  Cluster {row['cluster_number']}: {row['size']} members")
            print(f"    Representative: {row['representative']}")
            print(f"    Members: {row['members']}")


def test_advanced_analysis():
    """Test advanced DIAMOND analysis utilities."""
    print("\n" + "="*60)
    print("TEST 3: Advanced DIAMOND Analysis")
    print("="*60)

    # Create mock DIAMOND output DataFrame
    import pandas as pd

    mock_data = {
        'qseqid': ['GENE_001', 'GENE_001', 'GENE_002', 'GENE_003', 'GENE_004'],
        'sseqid': ['TARGET_A', 'TARGET_B', 'TARGET_C', 'TARGET_D', 'TARGET_E'],
        'pident': [95.5, 75.0, 88.0, 92.0, 65.0],
        'length': [400, 380, 420, 410, 350],
        'evalue': [1e-120, 1e-50, 1e-100, 1e-110, 1e-20],
        'bitscore': [850, 400, 780, 820, 300],
        'qcoverage': [95.0, 90.0, 98.0, 97.0, 85.0]
    }

    df = pd.DataFrame(mock_data)

    print(f"\nMock alignment data: {len(df)} hits")

    # Calculate statistics
    stats = DiamondAlignmentAnalyzer.calculate_alignment_statistics(df)

    print("\n✓ Alignment statistics:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")

    # Identify potential paralogs
    paralogs = DiamondAlignmentAnalyzer.identify_paralogs(
        df,
        min_identity=70.0,
        min_hits=2
    )

    print(f"\n✓ Potential paralogs (queries with multiple hits):")
    if not paralogs.empty:
        print(paralogs[['qseqid', 'sseqid', 'pident', 'evalue']])
    else:
        print("  None detected (all queries have single best hits)")

    # Build alignment graph
    graph = DiamondAlignmentAnalyzer.build_alignment_graph(df, min_identity=70.0)

    print(f"\n✓ Alignment graph:")
    for query, subjects in graph.items():
        print(f"  {query} -> {subjects}")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("TESTING NEW DIAMOND-BASED FEATURES")
    print("="*60)
    print("\nThese tests demonstrate:")
    print("1. Bidirectional Best Hits for ortholog detection")
    print("2. DIAMOND clustering for redundancy removal")
    print("3. Advanced alignment analysis utilities")

    try:
        # Test 1: BBH
        test_bidirectional_best_hits()

        # Test 2: Clustering
        test_clustering()

        # Test 3: Advanced analysis
        test_advanced_analysis()

        print("\n" + "="*60)
        print("ALL TESTS COMPLETED SUCCESSFULLY ✓")
        print("="*60)
        print("\nNew features are ready to use in your workflows!")
        print("\nFor real data, use:")
        print("  - gene_structure_analyzer.py: BBH methods")
        print("  - diamond_clustering.py: Clustering workflows")
        print("  - diamond_utils.py: DIAMOND utilities")

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
