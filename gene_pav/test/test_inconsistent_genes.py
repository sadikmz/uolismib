#!/usr/bin/env python3
"""
Generate mock data with genes that have transcripts in different quadrants
to test the inconsistent genes analysis functionality
"""
import pandas as pd
import numpy as np

# Create mock data with some genes having transcripts in different quadrants
mock_data = []

# Gene pair 1: Transcripts in "Present in both" and "Ref only"
mock_data.extend([
    {
        'old_gene': 'gene-MOCK_001', 'old_transcript': 'MOCK_001_t1',
        'new_gene': 'QMOCK_001', 'new_transcript': 'QMOCK_001_t1',
        'class_code': 'em', 'exons': 3, 'class_code_multi': 'em', 'class_type': 'ackmnj',
        'emckmnj': 1, 'emckmnje': 1,
        'query_total_ipr_domain_length': 500.0, 'ref_total_ipr_domain_length': 450.0
    },
    {
        'old_gene': 'gene-MOCK_001', 'old_transcript': 'MOCK_001_t2',
        'new_gene': 'QMOCK_001', 'new_transcript': 'QMOCK_001_t2',
        'class_code': 'em', 'exons': 2, 'class_code_multi': 'em', 'class_type': 'ackmnj',
        'emckmnj': 1, 'emckmnje': 1,
        'query_total_ipr_domain_length': np.nan, 'ref_total_ipr_domain_length': 300.0
    },
    {
        'old_gene': 'gene-MOCK_001', 'old_transcript': 'MOCK_001_t3',
        'new_gene': 'QMOCK_001', 'new_transcript': 'QMOCK_001_t3',
        'class_code': 'j', 'exons': 2, 'class_code_multi': 'j', 'class_type': 'ackmnj',
        'emckmnj': 1, 'emckmnje': 1,
        'query_total_ipr_domain_length': 480.0, 'ref_total_ipr_domain_length': 440.0
    },
])

# Gene pair 2: Transcripts in "Present in both" and "Query only"
mock_data.extend([
    {
        'old_gene': 'gene-MOCK_002', 'old_transcript': 'MOCK_002_t1',
        'new_gene': 'QMOCK_002', 'new_transcript': 'QMOCK_002_t1',
        'class_code': 'em', 'exons': 4, 'class_code_multi': 'em', 'class_type': 'ackmnj',
        'emckmnj': 1, 'emckmnje': 1,
        'query_total_ipr_domain_length': 600.0, 'ref_total_ipr_domain_length': 580.0
    },
    {
        'old_gene': 'gene-MOCK_002', 'old_transcript': 'MOCK_002_t2',
        'new_gene': 'QMOCK_002', 'new_transcript': 'QMOCK_002_t2',
        'class_code': 'em', 'exons': 3, 'class_code_multi': 'em', 'class_type': 'ackmnj',
        'emckmnj': 1, 'emckmnje': 1,
        'query_total_ipr_domain_length': 550.0, 'ref_total_ipr_domain_length': np.nan
    },
])

# Gene pair 3: Transcripts in "Absent in both" and "Present in both"
mock_data.extend([
    {
        'old_gene': 'gene-MOCK_003', 'old_transcript': 'MOCK_003_t1',
        'new_gene': 'QMOCK_003', 'new_transcript': 'QMOCK_003_t1',
        'class_code': 'em', 'exons': 2, 'class_code_multi': 'em', 'class_type': 'ackmnj',
        'emckmnj': 1, 'emckmnje': 1,
        'query_total_ipr_domain_length': np.nan, 'ref_total_ipr_domain_length': np.nan
    },
    {
        'old_gene': 'gene-MOCK_003', 'old_transcript': 'MOCK_003_t2',
        'new_gene': 'QMOCK_003', 'new_transcript': 'QMOCK_003_t2',
        'class_code': 'j', 'exons': 3, 'class_code_multi': 'j', 'class_type': 'ackmnj',
        'emckmnj': 1, 'emckmnje': 1,
        'query_total_ipr_domain_length': 400.0, 'ref_total_ipr_domain_length': 380.0
    },
    {
        'old_gene': 'gene-MOCK_003', 'old_transcript': 'MOCK_003_t3',
        'new_gene': 'QMOCK_003', 'new_transcript': 'QMOCK_003_t3',
        'class_code': 'n', 'exons': 2, 'class_code_multi': 'n', 'class_type': 'ackmnj',
        'emckmnj': 1, 'emckmnje': 1,
        'query_total_ipr_domain_length': np.nan, 'ref_total_ipr_domain_length': np.nan
    },
])

# Gene pair 4: Multiple transcripts with different combinations
mock_data.extend([
    {
        'old_gene': 'gene-MOCK_004', 'old_transcript': 'MOCK_004_t1',
        'new_gene': 'QMOCK_004', 'new_transcript': 'QMOCK_004_t1',
        'class_code': 'em', 'exons': 5, 'class_code_multi': 'em', 'class_type': 'ackmnj',
        'emckmnj': 1, 'emckmnje': 1,
        'query_total_ipr_domain_length': 700.0, 'ref_total_ipr_domain_length': 650.0
    },
    {
        'old_gene': 'gene-MOCK_004', 'old_transcript': 'MOCK_004_t2',
        'new_gene': 'QMOCK_004', 'new_transcript': 'QMOCK_004_t2',
        'class_code': 'j', 'exons': 4, 'class_code_multi': 'j', 'class_type': 'ackmnj',
        'emckmnj': 1, 'emckmnje': 1,
        'query_total_ipr_domain_length': np.nan, 'ref_total_ipr_domain_length': 600.0
    },
    {
        'old_gene': 'gene-MOCK_004', 'old_transcript': 'MOCK_004_t3',
        'new_gene': 'QMOCK_004', 'new_transcript': 'QMOCK_004_t3',
        'class_code': 'm', 'exons': 3, 'class_code_multi': 'm', 'class_type': 'ackmnj',
        'emckmnj': 1, 'emckmnje': 1,
        'query_total_ipr_domain_length': 680.0, 'ref_total_ipr_domain_length': np.nan
    },
    {
        'old_gene': 'gene-MOCK_004', 'old_transcript': 'MOCK_004_t4',
        'new_gene': 'QMOCK_004', 'new_transcript': 'QMOCK_004_t4',
        'class_code': 'n', 'exons': 2, 'class_code_multi': 'n', 'class_type': 'ackmnj',
        'emckmnj': 1, 'emckmnje': 1,
        'query_total_ipr_domain_length': np.nan, 'ref_total_ipr_domain_length': np.nan
    },
])

# Add some consistent gene pairs (all transcripts in same quadrant)
for i in range(5, 10):
    mock_data.extend([
        {
            'old_gene': f'gene-MOCK_{i:03d}', 'old_transcript': f'MOCK_{i:03d}_t1',
            'new_gene': f'QMOCK_{i:03d}', 'new_transcript': f'QMOCK_{i:03d}_t1',
            'class_code': 'em', 'exons': 3, 'class_code_multi': 'em', 'class_type': 'ackmnj',
            'emckmnj': 1, 'emckmnje': 1,
            'query_total_ipr_domain_length': 400.0 + i*10, 'ref_total_ipr_domain_length': 380.0 + i*10
        },
        {
            'old_gene': f'gene-MOCK_{i:03d}', 'old_transcript': f'MOCK_{i:03d}_t2',
            'new_gene': f'QMOCK_{i:03d}', 'new_transcript': f'QMOCK_{i:03d}_t2',
            'class_code': 'j', 'exons': 2, 'class_code_multi': 'j', 'class_type': 'ackmnj',
            'emckmnj': 1, 'emckmnje': 1,
            'query_total_ipr_domain_length': 410.0 + i*10, 'ref_total_ipr_domain_length': 390.0 + i*10
        },
    ])

# Create DataFrame
df_mock = pd.DataFrame(mock_data)

# Save to TSV
output_file = 'mock_data_inconsistent_genes.tsv'
df_mock.to_csv(output_file, sep='\t', index=False)
print(f"Created mock data: {output_file}")
print(f"Total rows: {len(df_mock)}")
print(f"Gene pairs: {df_mock[['old_gene', 'new_gene']].drop_duplicates().shape[0]}")
print("\nGene pairs with multiple transcripts:")
gene_pair_counts = df_mock.groupby(['old_gene', 'new_gene']).size().reset_index(name='count')
print(gene_pair_counts[gene_pair_counts['count'] > 1])
