#!/usr/bin/env python3
"""
Example Workflow: Gene Structure Change Analysis
=================================================
This script demonstrates the complete workflow with synthetic test data.
"""

import sys
from pathlib import Path
from gene_structure_analyzer import (
    GFFParser, BlastAnalyzer, GeneStructureAnalyzer, 
    ResultsExporter, Gene, BlastHit
)


def generate_test_data():
    """
    Generate synthetic test data to demonstrate the workflow.
    This creates example scenarios of gene splits and merges.
    """
    print("\n" + "="*60)
    print("GENERATING SYNTHETIC TEST DATA")
    print("="*60)
    
    # Create synthetic reference genes
    ref_genes = {
        # This gene will be split in the updated genome
        'REF_GENE_001': Gene(
            gene_id='REF_GENE_001',
            chromosome='chr1',
            start=1000,
            end=4000,  # 3000 bp
            strand='+',
            protein_seq='M' * 1000  # 1000 AA
        ),
        
        # These two genes will be merged in the updated genome
        'REF_GENE_002': Gene(
            gene_id='REF_GENE_002',
            chromosome='chr1',
            start=10000,
            end=11500,  # 1500 bp
            strand='+',
            protein_seq='M' * 500  # 500 AA
        ),
        'REF_GENE_003': Gene(
            gene_id='REF_GENE_003',
            chromosome='chr1',
            start=11600,
            end=13100,  # 1500 bp
            strand='+',
            protein_seq='M' * 500  # 500 AA
        ),
        
        # Control gene - no change
        'REF_GENE_004': Gene(
            gene_id='REF_GENE_004',
            chromosome='chr1',
            start=20000,
            end=22000,
            strand='+',
            protein_seq='M' * 666
        ),
        
        # Another split example
        'REF_GENE_005': Gene(
            gene_id='REF_GENE_005',
            chromosome='chr2',
            start=5000,
            end=9000,  # 4000 bp
            strand='-',
            protein_seq='M' * 1333
        )
    }
    
    # Create synthetic updated genes
    upd_genes = {
        # Split from REF_GENE_001
        'UPD_GENE_001A': Gene(
            gene_id='UPD_GENE_001A',
            chromosome='chr1',
            start=1000,
            end=2500,  # 1500 bp (first half)
            strand='+',
            protein_seq='M' * 500
        ),
        'UPD_GENE_001B': Gene(
            gene_id='UPD_GENE_001B',
            chromosome='chr1',
            start=2550,
            end=4000,  # 1450 bp (second half)
            strand='+',
            protein_seq='M' * 483
        ),
        
        # Merged from REF_GENE_002 and REF_GENE_003
        'UPD_GENE_002': Gene(
            gene_id='UPD_GENE_002',
            chromosome='chr1',
            start=10000,
            end=13100,  # Covers both original genes
            strand='+',
            protein_seq='M' * 1000
        ),
        
        # Control gene - no change (1:1 mapping)
        'UPD_GENE_004': Gene(
            gene_id='UPD_GENE_004',
            chromosome='chr1',
            start=20000,
            end=22000,
            strand='+',
            protein_seq='M' * 666
        ),
        
        # Split from REF_GENE_005 into 3 genes
        'UPD_GENE_005A': Gene(
            gene_id='UPD_GENE_005A',
            chromosome='chr2',
            start=5000,
            end=6300,
            strand='-',
            protein_seq='M' * 433
        ),
        'UPD_GENE_005B': Gene(
            gene_id='UPD_GENE_005B',
            chromosome='chr2',
            start=6400,
            end=7700,
            strand='-',
            protein_seq='M' * 433
        ),
        'UPD_GENE_005C': Gene(
            gene_id='UPD_GENE_005C',
            chromosome='chr2',
            start=7800,
            end=9000,
            strand='-',
            protein_seq='M' * 400
        )
    }
    
    print(f"\nCreated {len(ref_genes)} reference genes")
    print(f"Created {len(upd_genes)} updated genes")
    print("\nExpected changes:")
    print("  - 2 splits: REF_GENE_001 -> 2 genes, REF_GENE_005 -> 3 genes")
    print("  - 1 merge:  REF_GENE_002 + REF_GENE_003 -> 1 gene")
    print("  - 1 unchanged: REF_GENE_004")
    
    return ref_genes, upd_genes


def generate_blast_hits(ref_genes, upd_genes):
    """
    Generate synthetic BLAST hits representing the alignments.
    In real workflow, these come from running BLASTP.
    """
    print("\n" + "="*60)
    print("GENERATING SYNTHETIC BLAST RESULTS")
    print("="*60)
    
    forward_hits = []
    reverse_hits = []
    
    # Forward: REF -> UPD
    
    # Split: REF_GENE_001 -> UPD_GENE_001A and UPD_GENE_001B
    forward_hits.append(BlastHit(
        query_id='REF_GENE_001',
        subject_id='UPD_GENE_001A',
        pident=98.5,
        length=500,
        qstart=1,
        qend=500,
        qlen=1000,
        sstart=1,
        send=500,
        slen=500,
        evalue=0.0,
        bitscore=1000
    ))
    forward_hits.append(BlastHit(
        query_id='REF_GENE_001',
        subject_id='UPD_GENE_001B',
        pident=98.2,
        length=483,
        qstart=501,
        qend=1000,
        qlen=1000,
        sstart=1,
        send=483,
        slen=483,
        evalue=0.0,
        bitscore=950
    ))
    
    # Merge: REF_GENE_002 and REF_GENE_003 -> UPD_GENE_002
    forward_hits.append(BlastHit(
        query_id='REF_GENE_002',
        subject_id='UPD_GENE_002',
        pident=99.0,
        length=500,
        qstart=1,
        qend=500,
        qlen=500,
        sstart=1,
        send=500,
        slen=1000,
        evalue=0.0,
        bitscore=1000
    ))
    forward_hits.append(BlastHit(
        query_id='REF_GENE_003',
        subject_id='UPD_GENE_002',
        pident=99.0,
        length=500,
        qstart=1,
        qend=500,
        qlen=500,
        sstart=501,
        send=1000,
        slen=1000,
        evalue=0.0,
        bitscore=1000
    ))
    
    # 1:1 mapping: REF_GENE_004 -> UPD_GENE_004
    forward_hits.append(BlastHit(
        query_id='REF_GENE_004',
        subject_id='UPD_GENE_004',
        pident=100.0,
        length=666,
        qstart=1,
        qend=666,
        qlen=666,
        sstart=1,
        send=666,
        slen=666,
        evalue=0.0,
        bitscore=1300
    ))
    
    # Split: REF_GENE_005 -> UPD_GENE_005A, 005B, 005C
    forward_hits.append(BlastHit(
        query_id='REF_GENE_005',
        subject_id='UPD_GENE_005A',
        pident=97.5,
        length=433,
        qstart=1,
        qend=433,
        qlen=1333,
        sstart=1,
        send=433,
        slen=433,
        evalue=0.0,
        bitscore=850
    ))
    forward_hits.append(BlastHit(
        query_id='REF_GENE_005',
        subject_id='UPD_GENE_005B',
        pident=97.8,
        length=433,
        qstart=434,
        qend=866,
        qlen=1333,
        sstart=1,
        send=433,
        slen=433,
        evalue=0.0,
        bitscore=860
    ))
    forward_hits.append(BlastHit(
        query_id='REF_GENE_005',
        subject_id='UPD_GENE_005C',
        pident=98.0,
        length=400,
        qstart=867,
        qend=1333,
        qlen=1333,
        sstart=1,
        send=400,
        slen=400,
        evalue=0.0,
        bitscore=800
    ))
    
    # Reverse: UPD -> REF (reciprocal hits)
    
    # Reverse of split
    reverse_hits.append(BlastHit(
        query_id='UPD_GENE_001A',
        subject_id='REF_GENE_001',
        pident=98.5,
        length=500,
        qstart=1,
        qend=500,
        qlen=500,
        sstart=1,
        send=500,
        slen=1000,
        evalue=0.0,
        bitscore=1000
    ))
    reverse_hits.append(BlastHit(
        query_id='UPD_GENE_001B',
        subject_id='REF_GENE_001',
        pident=98.2,
        length=483,
        qstart=1,
        qend=483,
        qlen=483,
        sstart=501,
        send=1000,
        slen=1000,
        evalue=0.0,
        bitscore=950
    ))
    
    # Reverse of merge
    reverse_hits.append(BlastHit(
        query_id='UPD_GENE_002',
        subject_id='REF_GENE_002',
        pident=99.0,
        length=500,
        qstart=1,
        qend=500,
        qlen=1000,
        sstart=1,
        send=500,
        slen=500,
        evalue=0.0,
        bitscore=1000
    ))
    reverse_hits.append(BlastHit(
        query_id='UPD_GENE_002',
        subject_id='REF_GENE_003',
        pident=99.0,
        length=500,
        qstart=501,
        qend=1000,
        qlen=1000,
        sstart=1,
        send=500,
        slen=500,
        evalue=0.0,
        bitscore=1000
    ))
    
    # Reverse of 1:1
    reverse_hits.append(BlastHit(
        query_id='UPD_GENE_004',
        subject_id='REF_GENE_004',
        pident=100.0,
        length=666,
        qstart=1,
        qend=666,
        qlen=666,
        sstart=1,
        send=666,
        slen=666,
        evalue=0.0,
        bitscore=1300
    ))
    
    # Reverse of 3-way split
    reverse_hits.append(BlastHit(
        query_id='UPD_GENE_005A',
        subject_id='REF_GENE_005',
        pident=97.5,
        length=433,
        qstart=1,
        qend=433,
        qlen=433,
        sstart=1,
        send=433,
        slen=1333,
        evalue=0.0,
        bitscore=850
    ))
    reverse_hits.append(BlastHit(
        query_id='UPD_GENE_005B',
        subject_id='REF_GENE_005',
        pident=97.8,
        length=433,
        qstart=1,
        qend=433,
        qlen=433,
        sstart=434,
        send=866,
        slen=1333,
        evalue=0.0,
        bitscore=860
    ))
    reverse_hits.append(BlastHit(
        query_id='UPD_GENE_005C',
        subject_id='REF_GENE_005',
        pident=98.0,
        length=400,
        qstart=1,
        qend=400,
        qlen=400,
        sstart=867,
        send=1333,
        slen=1333,
        evalue=0.0,
        bitscore=800
    ))
    
    print(f"\nGenerated {len(forward_hits)} forward BLAST hits")
    print(f"Generated {len(reverse_hits)} reverse BLAST hits")
    
    return forward_hits, reverse_hits


def run_analysis(ref_genes, upd_genes, forward_hits, reverse_hits):
    """
    Run the complete gene structure change analysis.
    """
    print("\n" + "="*60)
    print("RUNNING GENE STRUCTURE ANALYSIS")
    print("="*60)
    
    # Initialize analyzer
    analyzer = GeneStructureAnalyzer(
        ref_genes=ref_genes,
        upd_genes=upd_genes,
        forward_blast=forward_hits,
        reverse_blast=reverse_hits
    )
    
    # Detect splits and merges
    splits = analyzer.detect_splits(min_confidence=0.7)
    merges = analyzer.detect_merges(min_confidence=0.7)
    
    return splits, merges


def main():
    """
    Main workflow execution.
    """
    print("\n" + "="*70)
    print(" "*10 + "GENE STRUCTURE CHANGE ANALYZER - TEST WORKFLOW")
    print("="*70)
    
    # Step 1: Generate test data
    ref_genes, upd_genes = generate_test_data()
    
    # Step 2: Generate BLAST results
    forward_hits, reverse_hits = generate_blast_hits(ref_genes, upd_genes)
    
    # Step 3: Run analysis
    splits, merges = run_analysis(ref_genes, upd_genes, forward_hits, reverse_hits)
    
    # Step 4: Display results
    ResultsExporter.print_summary(splits, merges)
    
    # Step 5: Verify results
    print("\n" + "="*60)
    print("VALIDATION")
    print("="*60)
    
    expected_splits = 2  # REF_GENE_001 and REF_GENE_005
    expected_merges = 1  # REF_GENE_002 + REF_GENE_003
    
    print(f"\nExpected splits: {expected_splits}")
    print(f"Detected splits: {len(splits)}")
    print(f"✓ PASS" if len(splits) == expected_splits else "✗ FAIL")
    
    print(f"\nExpected merges: {expected_merges}")
    print(f"Detected merges: {len(merges)}")
    print(f"✓ PASS" if len(merges) == expected_merges else "✗ FAIL")
    
    # Step 6: Export results
    print("\n" + "="*60)
    print("EXPORTING RESULTS")
    print("="*60)
    
    if splits:
        ResultsExporter.save_results(splits, 'gene_splits.tsv')

    if merges:
        ResultsExporter.save_results(merges, 'gene_merges.tsv')
    
    # Display detailed information for each detected change
    print("\n" + "="*60)
    print("DETAILED RESULTS")
    print("="*60)
    
    if splits:
        print("\n--- Detected Splits ---")
        for i, split in enumerate(splits, 1):
            print(f"\n{i}. {split.ref_genes[0]} → {', '.join(split.updated_genes)}")
            print(f"   Confidence: {split.confidence_score:.3f}")
            print(f"   Evidence:")
            print(f"     - Reciprocal hits: {split.evidence['reciprocal']}")
            print(f"     - Adjacent genes: {split.evidence['adjacent']}")
            print(f"     - Coverage: {split.evidence['coverage']:.2%}")
            print(f"     - Ref length: {split.evidence['ref_length']} bp")
            print(f"     - Updated lengths: {split.evidence['updated_lengths']} bp")
    
    if merges:
        print("\n--- Detected Merges ---")
        for i, merge in enumerate(merges, 1):
            print(f"\n{i}. {', '.join(merge.ref_genes)} → {merge.updated_genes[0]}")
            print(f"   Confidence: {merge.confidence_score:.3f}")
            print(f"   Evidence:")
            print(f"     - Reciprocal hits: {merge.evidence['reciprocal']}")
            print(f"     - Adjacent genes: {merge.evidence['adjacent']}")
            print(f"     - Coverage: {merge.evidence['coverage']:.2%}")
            print(f"     - Ref lengths: {merge.evidence['ref_lengths']} bp")
            print(f"     - Updated length: {merge.evidence['updated_length']} bp")
    
    print("\n" + "="*70)
    print("WORKFLOW COMPLETED SUCCESSFULLY!")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
