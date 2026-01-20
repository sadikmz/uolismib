#!/usr/bin/env python3
"""
PAVprot - Presence/Absence Variation Protein Analysis Pipeline

Analyzes gene mapping relationships between reference and query genomes,
integrating GffCompare tracking data, DIAMOND BLASTP alignments, and
InterProScan domain annotations.

Features:
    - Parse GffCompare tracking files to extract gene/transcript mappings
    - Classify mappings at transcript, gene, and gene-pair levels
    - Detect one-to-many and many-to-one gene relationships
    - Integrate DIAMOND BLASTP protein sequence alignments
    - Integrate InterProScan domain annotations
    - Filter output by exact match, 1:1 mappings, or class type

Usage:
    python pavprot.py --gff-comp tracking.txt --gff ref.gff3 [options]

Example:
    python pavprot.py --gff-comp gffcompare.tracking --gff ref.gff3,query.gff3 \\
        --run-diamond --ref-faa ref.faa --qry-faa query.faa \\
        --filter-exact-match --output-dir results/

Output:
    Creates a pavprot_out/ directory (or specified --output-dir) containing:
    - synonym_mapping_liftover_gffcomp.tsv: Main output with all metrics
    - *_ref_to_multiple_query.tsv: One-to-many mapping analysis
    - *_query_to_multiple_ref.tsv: Many-to-one mapping analysis
    - *_multiple_mappings_summary.txt: Summary statistics
"""

from collections import defaultdict
from typing import Dict, List, Tuple, Set, Optional, Iterator
import argparse
import sys
import os
import subprocess
import gzip
import pandas as pd
from pathlib import Path

# Import InterProParser and run_interproscan from same directory
from parse_interproscan import InterProParser, run_interproscan
from mapping_multiplicity import detect_multiple_mappings
from bidirectional_best_hits import BidirectionalBestHits, enrich_pavprot_with_bbh
from pairwise_align_prot import local_alignment_similarity, read_all_sequences
from gsmc import (
    get_cdi_genes,
    detect_one_to_one_orthologs,
    detect_one_to_many,
    detect_many_to_one,
    detect_complex_one_to_many,
    classify_cross_mappings,
    detect_unmapped_genes
)

class PAVprot:
    @staticmethod
    def fasta2dict(source: str, is_query: bool = False):
        """
        Parse FASTA file and yield (header, sequence) tuples.

        Args:
            source: Path to FASTA file or '-' for stdin
            is_query: If True, strip '-pN' suffix from transcript IDs

        Yields:
            Tuple of (transcript_id, sequence)
        """
        if str(source) == '-':
            context = sys.stdin
        else:
            context = open(source, 'r')

        with context:
            current_header = None
            current_seq = []

            for line in context:
                line = line.rstrip('\n')
                if not line:
                    continue

                if line.startswith('>'):
                    if current_header:
                        yield current_header, ''.join(current_seq)

                    header = line[1:].strip()
                    transcript_id = header.split()[0].split('|')[0]

                    if is_query:
                        if len(transcript_id) >= 3 and transcript_id[-3] == '-' and transcript_id[-2] == 'p':
                            transcript_id = transcript_id[:-3]

                    current_header = transcript_id
                    current_seq = []
                else:
                    current_seq.append(line.upper())

            if current_header:
                yield current_header, ''.join(current_seq)

    @staticmethod
    def load_gff(gff_path: str) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        Parse GFF3 file to extract RNA-to-protein and locus-to-gene mappings.

        Args:
            gff_path: Path to GFF3 file

        Returns:
            Tuple of (rna_to_protein, locus_to_gene) dictionaries
        """
        rna_to_protein: Dict[str, str] = {}
        locus_to_gene: Dict[str, str] = {}

        with open(gff_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '\tCDS\t' not in line:
                    continue
                attrs = line.split('\t')[8]
                attr_dict = {}
                for pair in attrs.split(';'):
                    if '=' in pair:
                        k, v = pair.split('=', 1)
                        attr_dict[k] = v

                parent = attr_dict.get('Parent', '')
                if parent.startswith('rna-'):
                    rna_id = parent[4:]
                    protein_id = attr_dict.get('GenBank') or attr_dict.get('protein_id')
                    if protein_id:
                        rna_to_protein[rna_id] = protein_id

                locus_tag = attr_dict.get('locus_tag', '')
                if locus_tag:
                    gene_id = f"gene-{locus_tag}"
                    locus_to_gene[locus_tag] = gene_id

        return rna_to_protein, locus_to_gene

    @classmethod
    def parse_tracking(
        cls,
        filepath: str,
        feature_table: Optional[str] = None,
        filter_codes: Optional[Set[str]] = None
    ) -> Tuple[Dict[str, List[dict]], Dict[str, List[dict]]]:
        """
        Parse GffCompare tracking file and extract gene/transcript mappings.

        Args:
            filepath: Path to tracking file
            feature_table: Optional path to GFF3 feature table for ID mapping
            filter_codes: Optional set of class codes to filter by

        Returns:
            Tuple of (full_dict, filtered_dict) where each is a dict mapping
            ref_gene to list of entry dictionaries
        """
        rna_to_protein, locus_to_gene = {}, {}
        if feature_table:
            rna_to_protein, locus_to_gene = cls.load_gff(feature_table)

        full_dict = defaultdict(list)
        filtered_dict = defaultdict(list)
        filter_codes = filter_codes or set()

        with open(filepath) as f:
            for line in f:
                line = line.rstrip('\n')
                if not line or line.startswith('#'):
                    continue
                fields = line.split('\t')
                if len(fields) < 5:
                    continue
                ref_field = fields[2].strip()
                if ref_field == '-' or '|' not in ref_field:
                    continue

                class_code = fields[3].strip()
                if class_code == '=':
                    class_code = 'em'

                query_info = fields[4].strip()
                parts = query_info.split('|')
                if len(parts) < 3:
                    continue

                ref_gene_raw, ref_trans_raw = [x.strip() for x in ref_field.split('|')]
                ref_trans_clean = ref_trans_raw.replace('rna-', '')
                ref_trans_final = rna_to_protein.get(ref_trans_clean, ref_trans_clean)
                ref_gene = locus_to_gene.get(ref_gene_raw, ref_gene_raw)

                q_gene_full = parts[0]
                q_gene = q_gene_full.split(':')[-1]
                q_trans = parts[1]
                try:
                    exons = int(parts[2])
                except ValueError:
                    exons = None

                entry = {
                    "ref_gene": ref_gene,
                    "ref_transcript": ref_trans_final,
                    "query_gene": q_gene,
                    "query_transcript": q_trans,
                    "class_code": class_code,
                    "exons": exons
                }

                full_dict[ref_gene].append(entry)
                if not filter_codes or class_code in filter_codes:
                    filtered_dict[ref_gene].append(entry)

        return dict(full_dict), dict(filtered_dict)


    @staticmethod
    def _assign_class_type(class_codes: set) -> str:
        """
        Assign class_type based on class codes (for visualization purpose):
            a → em only
            ckmnj → c,k,m,n,j only
            e → e only
            ackmnj → em,c,k,m,n,j
            ackmnje → em,c,k,m,n,j,e
            o → o only
            sx → s,x
            iy → i,y
            pru → anything else (p,r,u)
        """
        if class_codes <= {'em'}:
            return 'a'
        elif class_codes <= {'c', 'k', 'm', 'n', 'j'}:
            return 'ckmnj'
        elif class_codes <= {'e'}:
            return 'e'
        elif class_codes <= {'em', 'c', 'k', 'm', 'n', 'j'}:
            return 'ackmnj'
        elif class_codes <= {'em', 'c', 'k', 'm', 'n', 'j', 'e'}:
            return 'ackmnje'
        elif class_codes <= {'o'}:
            return 'o'
        elif class_codes <= {'s', 'x'}:
            return 'sx'
        elif class_codes <= {'i', 'y'}:
            return 'iy'
        else:
            return 'pru'

    @classmethod
    def compute_all_metrics(cls, full_dict: dict) -> dict:
        """
        Compute all metrics in a single pass through the data.

        This unified method combines what was previously done in two separate methods
        (filter_multi_transcripts and add_gene_pair_metrics) for better performance.

        Computes:
            Query-gene level:
                - class_code_multi_query: aggregated class codes for query_gene
                - class_type_transcript: class_type based on query_gene aggregation
                - ackmnj: 1 if any code in {em,c,k,m,n,j}
                - ackmnje: 1 if any code in {em,c,k,m,n,j,e}

            Ref-gene level:
                - class_code_multi_ref: aggregated class codes for ref_gene

            Gene-pair level:
                - class_code_pair: aggregated class codes for (ref_gene, query_gene) pair
                - class_type_gene: class_type at gene-pair level
                - exact_match: 1 if ALL transcripts in pair are 'em'
                - ref_multi_transcript: 1 if ref_gene has >1 transcripts globally
                - qry_multi_transcript: 1 if query_gene has >1 transcripts globally
                - ref_multi_query: 0=exclusive 1:1, 1=one-to-many, 2=partner has others
                - qry_multi_ref: 0=exclusive 1:1, 1=many-to-one, 2=partner has others
                - ref_query_count: number of query genes this ref maps to
                - qry_ref_count: number of ref genes this query maps to

        Args:
            full_dict: Dictionary of entries keyed by ref_gene

        Returns:
            Updated full_dict with all metrics added to each entry
        """
        # =====================================================================
        # Single pass: Collect all groupings
        # =====================================================================
        query_gene_to_entries = defaultdict(list)
        ref_gene_to_entries = defaultdict(list)
        gene_pair_entries = defaultdict(list)
        ref_gene_transcripts = defaultdict(set)
        qry_gene_transcripts = defaultdict(set)
        ref_to_queries = defaultdict(set)
        qry_to_refs = defaultdict(set)

        for entries in full_dict.values():
            for entry in entries:
                ref_gene = entry['ref_gene']
                qry_gene = entry['query_gene']

                # Group by query_gene and ref_gene
                query_gene_to_entries[qry_gene].append(entry)
                ref_gene_to_entries[ref_gene].append(entry)

                # Group by gene pair
                gene_pair_entries[(ref_gene, qry_gene)].append(entry)

                # Collect transcripts per gene (global counting)
                ref_gene_transcripts[ref_gene].add(entry['ref_transcript'])
                qry_gene_transcripts[qry_gene].add(entry['query_transcript'])

                # Track gene-level mappings
                ref_to_queries[ref_gene].add(qry_gene)
                qry_to_refs[qry_gene].add(ref_gene)

        # =====================================================================
        # Compute query-gene level metrics
        # =====================================================================
        query_gene_info = {}
        for qgene, qentries in query_gene_to_entries.items():
            class_codes = {e['class_code'] for e in qentries}
            code_str = ';'.join(sorted(class_codes))
            ctype = cls._assign_class_type(class_codes)
            ackmnj = 1 if class_codes & {'em', 'c', 'k', 'm', 'n', 'j'} else 0
            ackmnje = 1 if class_codes & {'em', 'c', 'k', 'm', 'n', 'j', 'e'} else 0

            query_gene_info[qgene] = {
                'class_code_multi_query': code_str,
                'class_type_transcript': ctype,
                'ackmnj': ackmnj,
                'ackmnje': ackmnje
            }

        # =====================================================================
        # Compute ref-gene level metrics
        # =====================================================================
        ref_gene_info = {}
        for rgene, rentries in ref_gene_to_entries.items():
            class_codes = {e['class_code'] for e in rentries}
            code_str = ';'.join(sorted(class_codes))
            ref_gene_info[rgene] = {'class_code_multi_ref': code_str}

        # =====================================================================
        # Compute gene-pair level metrics
        # =====================================================================
        gene_pair_metrics = {}
        for (ref_gene, qry_gene), pair_entries in gene_pair_entries.items():
            class_codes = {e['class_code'] for e in pair_entries}
            exact_match = 1 if class_codes == {'em'} else 0
            class_code_pair = ';'.join(sorted(class_codes))
            class_type_gene = cls._assign_class_type(class_codes)

            num_queries_for_ref = len(ref_to_queries[ref_gene])
            num_refs_for_qry = len(qry_to_refs[qry_gene])

            # ref_multi_query encoding
            if num_queries_for_ref > 1:
                ref_multi_query = 1
            elif num_refs_for_qry > 1:
                ref_multi_query = 2
            else:
                ref_multi_query = 0

            # qry_multi_ref encoding
            if num_refs_for_qry > 1:
                qry_multi_ref = 1
            elif num_queries_for_ref > 1:
                qry_multi_ref = 2
            else:
                qry_multi_ref = 0

            gene_pair_metrics[(ref_gene, qry_gene)] = {
                'exact_match': exact_match,
                'class_code_pair': class_code_pair,
                'class_type_gene': class_type_gene,
                'ref_multi_query': ref_multi_query,
                'qry_multi_ref': qry_multi_ref,
                'ref_query_count': num_queries_for_ref,
                'qry_ref_count': num_refs_for_qry
            }

        # =====================================================================
        # Attach all metrics back to entries (single final pass)
        # =====================================================================
        for entries in full_dict.values():
            for entry in entries:
                ref_gene = entry['ref_gene']
                qry_gene = entry['query_gene']

                # Query gene metrics
                qinfo = query_gene_info.get(qry_gene, {
                    'class_code_multi_query': entry['class_code'],
                    'class_type_transcript': 'pru',
                    'ackmnj': 0,
                    'ackmnje': 0
                })
                entry['class_code_multi_query'] = qinfo['class_code_multi_query']
                entry['class_type_transcript'] = qinfo['class_type_transcript']
                entry['ackmnj'] = qinfo['ackmnj']
                entry['ackmnje'] = qinfo['ackmnje']

                # Ref gene metrics
                rinfo = ref_gene_info.get(ref_gene, {'class_code_multi_ref': entry['class_code']})
                entry['class_code_multi_ref'] = rinfo['class_code_multi_ref']

                # Multi-transcript flags
                entry['ref_multi_transcript'] = 1 if len(ref_gene_transcripts[ref_gene]) > 1 else 0
                entry['qry_multi_transcript'] = 1 if len(qry_gene_transcripts[qry_gene]) > 1 else 0

                # Gene pair metrics
                pair_metrics = gene_pair_metrics.get((ref_gene, qry_gene), {})
                entry['exact_match'] = pair_metrics.get('exact_match', 0)
                entry['class_code_pair'] = pair_metrics.get('class_code_pair', entry['class_code'])
                entry['class_type_gene'] = pair_metrics.get('class_type_gene', 'pru')
                entry['ref_multi_query'] = pair_metrics.get('ref_multi_query', 0)
                entry['qry_multi_ref'] = pair_metrics.get('qry_multi_ref', 0)
                entry['ref_query_count'] = pair_metrics.get('ref_query_count', 1)
                entry['qry_ref_count'] = pair_metrics.get('qry_ref_count', 1)

        return full_dict

    @classmethod
    def load_extra_copy_numbers(cls, liftoff_gff: str):
        """
        Parse Liftoff GFF3 (mRNA features) and extract extra_copy_number
        Returns: {query_transcript_id: int(extra_copy_number)}
        """
        extra_copy = {}

        if not liftoff_gff or not os.path.exists(liftoff_gff):
            return extra_copy

        with open(liftoff_gff) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '\tmRNA\t' not in line:
                    continue

                cols = line.split('\t')
                if len(cols) < 9:
                    continue

                attrs = cols[8]
                transcript_id = None
                copy_number = None

                for pair in attrs.split(';'):
                    if '=' not in pair:
                        continue
                    k, v = pair.split('=', 1)

                    if k == 'ID':
                        # Extract transcript ID (e.g. from "ID=FOZG_02018-t36_1")
                        transcript_id = v.split('.')[0]  # remove version if present
                    elif k.lower() == 'extra_copy_number':
                        try:
                            copy_number = int(v)
                        except ValueError:
                            copy_number = None

                if transcript_id and copy_number is not None:
                    extra_copy[transcript_id] = copy_number

        return extra_copy

    @classmethod
    def filter_extra_copy_transcripts(cls, full_dict: dict, liftoff_gff: str = None):
        """
        Add extra_copy_number from Liftoff GFF3 to entries based on query_transcript
        """
        extra_copy_map = cls.load_extra_copy_numbers(liftoff_gff)

        for entries in full_dict.values():
            for entry in entries:
                q_trans = entry["query_transcript"]
                copy_num = extra_copy_map.get(q_trans, 0)  # default 0 if not found
                entry["extra_copy_number"] = copy_num

        return full_dict

    @classmethod
    def load_interproscan_data(cls, interproscan_tsv: str) -> dict:
        """
        Load InterProScan data and extract domain information for each protein.

        Can load either:
        - Raw InterProScan TSV output (15 columns, no header)
        - Processed parse_interproscan output (with header, longest_ipr_domains files)

        Returns:
            Dictionary mapping protein_accession to:
            {
                'analysis': analysis type (from longest IPR domain),
                'signature_accession': signature accession (from longest IPR domain),
                'total_IPR_domain_length': sum of all IPR domain lengths
            }
        """
        if not interproscan_tsv or not os.path.exists(interproscan_tsv):
            return {}

        # Check if file has header by reading first line
        with open(interproscan_tsv, 'r') as f:
            first_line = f.readline().strip()

        has_header = 'protein_accession' in first_line or 'gene_id' in first_line

        if has_header:
            # Read processed output file with header
            df = pd.read_csv(interproscan_tsv, sep='\t')

            # Check if this is already a longest_ipr_domains file (has longestIPRdom or signature_description duplicated)
            if 'interpro_accession' in df.columns:
                # Filter to only IPR domains
                ipr_df = df[df['interpro_accession'].str.startswith('IPR', na=False)].copy()

                if len(ipr_df) == 0:
                    return {}

                # Calculate domain length
                ipr_df['domain_length'] = ipr_df['stop_location'] - ipr_df['start_location'] + 1
            else:
                # This might be a domain_distribution file without IPR filtering already done
                print(f"Warning: File {interproscan_tsv} doesn't appear to be an InterProScan output file")
                return {}
        else:
            # Parse raw InterProScan file (no header)
            parser = InterProParser()
            df = parser.parse_tsv(interproscan_tsv)

            # Filter to only IPR domains
            ipr_df = df[df['interpro_accession'].str.startswith('IPR', na=False)].copy()

            if len(ipr_df) == 0:
                return {}

            # Calculate domain length
            ipr_df['domain_length'] = ipr_df['stop_location'] - ipr_df['start_location'] + 1

        result = {}

        for protein_acc in ipr_df['protein_accession'].unique():
            protein_data = ipr_df[ipr_df['protein_accession'] == protein_acc]

            # Get longest IPR domain info (for analysis and signature)
            # Calculate individual domain lengths first
            protein_data = protein_data.copy()
            protein_data['domain_length'] = protein_data['stop_location'] - protein_data['start_location'] + 1
            longest_idx = protein_data['domain_length'].idxmax()
            longest_domain = protein_data.loc[longest_idx]

            # Calculate total IPR domain coverage with overlap handling
            intervals = list(zip(protein_data['start_location'], protein_data['stop_location']))
            total_length = cls._calculate_interval_coverage(intervals)

            result[protein_acc] = {
                'analysis': longest_domain['analysis'],
                'signature_accession': longest_domain['signature_accession'],
                'total_IPR_domain_length': int(total_length)
            }

        return result

    @staticmethod
    def _calculate_interval_coverage(intervals: list) -> int:
        """
        Calculate total coverage by merging overlapping intervals.

        Args:
            intervals: List of tuples (start, end) where coordinates are inclusive

        Returns:
            Total length covered (sum of merged interval lengths)
        """
        if not intervals:
            return 0

        # Sort intervals by start position
        sorted_intervals = sorted(intervals, key=lambda x: (x[0], x[1]))

        # Merge overlapping intervals
        merged = []
        current_start, current_end = sorted_intervals[0]

        for start, end in sorted_intervals[1:]:
            # Check if intervals overlap or are adjacent
            if start <= current_end + 1:
                # Overlapping or adjacent - extend current interval
                current_end = max(current_end, end)
            else:
                # No overlap - save current interval and start new one
                merged.append((current_start, current_end))
                current_start, current_end = start, end

        # Add the last interval
        merged.append((current_start, current_end))

        # Calculate total length (inclusive coordinates)
        total_length = sum(end - start + 1 for start, end in merged)

        return total_length

    @classmethod
    def enrich_interproscan_data(cls, data: dict, qry_interproscan_map: dict, ref_interproscan_map: dict):
        """
        Add InterProScan total IPR domain length to the data dictionary.

        Args:
            data: The main data dictionary to enrich
            qry_interproscan_map: Query gene_id -> total_iprdom_len mapping
            ref_interproscan_map: Reference gene_id -> total_iprdom_len mapping
        """
        for entries in data.values():
            for entry in entries:
                # Add query InterProScan data (map by query_gene)
                qry_gene = entry['query_gene']
                if qry_gene in qry_interproscan_map:
                    entry['query_gene_total_iprdom_len'] = qry_interproscan_map[qry_gene]
                else:
                    entry['query_gene_total_iprdom_len'] = 0

                # Add reference InterProScan data (map by ref_gene)
                ref_gene = entry['ref_gene']
                if ref_gene in ref_interproscan_map:
                    entry['ref_gene_total_iprdom_len'] = ref_interproscan_map[ref_gene]
                else:
                    entry['ref_gene_total_iprdom_len'] = 0

        return data

    @classmethod
    def detect_interproscan_type(cls, data: dict, interproscan_tsv: str) -> str:
        """
        Auto-detect whether InterProScan file matches reference or query transcripts.

        Args:
            data: The main data dictionary with ref_transcript and query_transcript
            interproscan_tsv: Path to InterProScan TSV file

        Returns:
            'reference' if InterProScan matches reference transcripts
            'query' if InterProScan matches query transcripts
            'unknown' if no clear match
        """
        if not interproscan_tsv or not os.path.exists(interproscan_tsv):
            return 'unknown'

        # Collect all reference and query transcript IDs from tracking data
        ref_transcripts = set()
        query_transcripts = set()
        query_genes = set()

        for entries in data.values():
            for entry in entries:
                ref_transcripts.add(entry['ref_transcript'])
                query_transcripts.add(entry['query_transcript'])
                query_genes.add(entry['query_gene'])

        # Load protein IDs from InterProScan file
        interpro_proteins = set()

        # Check if file has header
        with open(interproscan_tsv, 'r') as f:
            first_line = f.readline().strip()

        has_header = 'protein_accession' in first_line or 'gene_id' in first_line

        if has_header:
            df = pd.read_csv(interproscan_tsv, sep='\t', usecols=[0])
            interpro_proteins = set(df.iloc[:, 0].unique())
        else:
            # Raw InterProScan format (column 0 is protein_accession)
            with open(interproscan_tsv, 'r') as f:
                for line in f:
                    if line.strip():
                        protein_id = line.split('\t')[0]
                        interpro_proteins.add(protein_id)

        # Count matches
        ref_matches = len(interpro_proteins & ref_transcripts)
        query_matches = len(interpro_proteins & query_transcripts)
        query_gene_matches = len(interpro_proteins & query_genes)

        # Combine query transcript and gene matches
        total_query_matches = query_matches + query_gene_matches

        print(f"  → InterProScan auto-detection:", file=sys.stderr)
        print(f"     Reference transcript matches: {ref_matches}/{len(ref_transcripts)}", file=sys.stderr)
        print(f"     Query transcript matches: {query_matches}/{len(query_transcripts)}", file=sys.stderr)
        print(f"     Query gene matches: {query_gene_matches}/{len(query_genes)}", file=sys.stderr)

        # Determine type based on match counts
        if ref_matches > total_query_matches:
            print(f"  → Detected as: REFERENCE", file=sys.stderr)
            return 'reference'
        elif total_query_matches > ref_matches:
            print(f"  → Detected as: QUERY", file=sys.stderr)
            return 'query'
        else:
            print(f"  → Could not auto-detect (defaulting to: REFERENCE)", file=sys.stderr)
            return 'reference'  # Default to reference if unclear

class DiamondRunner:
    def __init__(self, threads: int = 40, output_prefix: str = "synonym_mapping_liftover_gffcomp", output_dir: str = "pavprot_out"):
        self.threads = threads
        self.output_prefix = output_prefix
        self.output_dir = output_dir
        self.fwd_diamond_path: str = None  # query -> ref (forward)
        self.rev_diamond_path: str = None  # ref -> query (reverse)

    def _run_diamond(self, db_path: str, query_path: str, output_name: str) -> str:
        """Run DIAMOND blastp with standard parameters."""
        out_dir = os.path.join(os.getcwd(), self.output_dir, 'compareprot_out')
        os.makedirs(out_dir, exist_ok=True)
        diamond_out = os.path.join(out_dir, f"{self.output_prefix}_{output_name}.tsv.gz")

        cmd_str = (
            f"diamond blastp "
            f"--db {db_path} "
            f"--query {query_path} "
            f"--ultra-sensitive "
            f"--masking none "
            f"--out {diamond_out} "
            f"--outfmt 6 qseqid qlen sallseqid slen qstart qend sstart send evalue bitscore score length pident nident mismatch gapopen gaps qcovhsp scovhsp qstrand "
            f"--evalue 1e-6 "
            f"--threads {self.threads} "
            f"--max-hsps 1 "
            f"--unal 1 "
            f"--compress 1"
        )

        print(f"Running DIAMOND blastp → {diamond_out}", file=sys.stderr)
        subprocess.run(cmd_str, shell=True, check=True)

        return diamond_out

    def diamond_blastp(self, ref_faa_path: str, qry_faa_path: str) -> str:
        """Run forward DIAMOND blastp (query -> reference)."""
        self.fwd_diamond_path = self._run_diamond(
            db_path=ref_faa_path,
            query_path=qry_faa_path,
            output_name="diamond_blastp_fwd"
        )
        return self.fwd_diamond_path

    def diamond_blastp_reverse(self, ref_faa_path: str, qry_faa_path: str) -> str:
        """Run reverse DIAMOND blastp (reference -> query) for BBH analysis."""
        self.rev_diamond_path = self._run_diamond(
            db_path=qry_faa_path,
            query_path=ref_faa_path,
            output_name="diamond_blastp_rev"
        )
        return self.rev_diamond_path

    def run_bidirectional(self, ref_faa_path: str, qry_faa_path: str) -> Tuple[str, str]:
        """
        Run bidirectional DIAMOND blastp for BBH analysis.

        Returns:
            Tuple of (forward_path, reverse_path)
        """
        print(f"\nRunning bidirectional DIAMOND for BBH analysis...", file=sys.stderr)
        fwd = self.diamond_blastp(ref_faa_path, qry_faa_path)
        rev = self.diamond_blastp_reverse(ref_faa_path, qry_faa_path)
        return fwd, rev

    def enrich_blastp(self, data: dict, diamond_tsv_gz: str):
        """Parse DIAMOND output and enrich the dictionary"""
        hits = {}
        with gzip.open(diamond_tsv_gz, 'rt') as f:
            for line in f:
                if not line.strip():
                    continue
                parts = line.strip().split('\t')
                hit = {
                    "qseqid": parts[0], "qlen": int(parts[1]), "sallseqid": parts[2], "slen": int(parts[3]),
                    "qstart": int(parts[4]), "qend": int(parts[5]), "sstart": int(parts[6]), "send": int(parts[7]),
                    "evalue": float(parts[8]), "bitscore": float(parts[9]), "score": float(parts[10]),
                    "length": int(parts[11]), "pident": float(parts[12]), "nident": int(parts[13]),
                    "mismatch": int(parts[14]), "gapopen": int(parts[15]), "gaps": int(parts[16]),
                    "qcovhsp": float(parts[17]), "scovhsp": float(parts[18]), "qstrand": parts[19]
                }
                qid = hit["qseqid"]
                if qid not in hits or hit["bitscore"] > hits[qid]["bitscore"]:
                    hits[qid] = hit
        
        # add pidentCov_9090
        query_to_high_hits = defaultdict(list)
        
        for hit in hits.values():
            if hit["pident"] >= 90.0 and hit["qcovhsp"] >= 90.0:
                query_to_high_hits[hit["qseqid"]].append(hit['sallseqid'])
       
        # Only keep query transcripts with multiple high-quality hits
        multi_match_queries = {q for q, refs in query_to_high_hits.items() if len(refs) > 1} 

        for entries in data.values():
            for entry in entries:
                qid = entry["query_transcript"]
                if qid in hits:
                    h = hits[qid]
                    entry["diamond"] = h
                    entry['pident'] = h['pident']
                    entry['qcovhsp'] = h['qcovhsp']
                    entry['scovhsp'] = h['scovhsp']
                    entry["identical_aa"] = h["nident"]
                    entry["mismatched_aa"] = h["mismatch"]
                    entry["indels_aa"] = h["gaps"]
                    entry["aligned_aa"] = h["length"]
                else:
                    entry["diamond"] = None
                    entry["identical_aa"] = entry["mismatched_aa"] = entry["indels_aa"] = entry["aligned_aa"] = entry['pident'] = entry['qcovhsp'] = entry['scovhsp'] = 0
                
                # add pidentCov_9090 info 
                if qid in multi_match_queries:
                    matching_refs = query_to_high_hits[qid]
                    entry['pidentCov_9090'] = {"ref_cnt": len(matching_refs), 
                                               "ref_trans": matching_refs}
                else:
                    entry['pidentCov_9090'] = None

        return data


def enrich_pairwise_alignment(data: dict, ref_faa: str, qry_faa: str) -> dict:
    """
    Enrich PAVprot data with Biopython pairwise alignment results.

    Performs local alignment for each transcript pair and adds:
    - pairwise_identity: Percent identity from local alignment
    - pairwise_coverage_ref: Coverage of reference sequence
    - pairwise_coverage_query: Coverage of query sequence
    - pairwise_aligned_length: Length of alignment

    Args:
        data: PAVprot data dictionary (ref_gene -> list of entries)
        ref_faa: Path to reference protein FASTA
        qry_faa: Path to query protein FASTA

    Returns:
        Enriched data dictionary
    """
    print("Loading sequences for pairwise alignment...", file=sys.stderr)
    ref_seqs = read_all_sequences(ref_faa)
    qry_seqs = read_all_sequences(qry_faa)
    print(f"  Loaded {len(ref_seqs)} reference, {len(qry_seqs)} query sequences", file=sys.stderr)

    # Count total pairs for progress
    total_pairs = sum(len(entries) for entries in data.values())
    completed = 0
    aligned_count = 0

    print(f"Running pairwise alignments for {total_pairs} transcript pairs...", file=sys.stderr)

    for entries in data.values():
        for entry in entries:
            ref_trans = entry.get('ref_transcript', '')
            qry_trans = entry.get('query_transcript', '')

            # Get sequences
            ref_seq = ref_seqs.get(ref_trans)
            qry_seq = qry_seqs.get(qry_trans)

            if ref_seq is not None and qry_seq is not None:
                # Perform local alignment
                result = local_alignment_similarity(str(ref_seq), str(qry_seq))
                entry['pairwise_identity'] = result.identity_percent
                entry['pairwise_coverage_ref'] = result.coverage_ref
                entry['pairwise_coverage_query'] = result.coverage_query
                entry['pairwise_aligned_length'] = result.aligned_length
                aligned_count += 1
            else:
                # Sequence not found - set to NA
                entry['pairwise_identity'] = None
                entry['pairwise_coverage_ref'] = None
                entry['pairwise_coverage_query'] = None
                entry['pairwise_aligned_length'] = None

            completed += 1
            if completed % 500 == 0:
                print(f"  Progress: {completed}/{total_pairs} pairs...", file=sys.stderr)

    print(f"  Completed {aligned_count} alignments out of {total_pairs} pairs", file=sys.stderr)
    return data


# =========================================================================
# Helper functions for main() - refactored for readability
# =========================================================================

def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for PAVprot."""
    parser = argparse.ArgumentParser(description="PAVprot – complete class-based pipeline")

    # Core inputs
    parser.add_argument('--gff-comp', required=True)
    parser.add_argument('--gff', help="GFF3 CDS feature table. Single GFF for reference only, or comma-separated 'ref.gff,query.gff' for both")
    parser.add_argument('--liftoff-gff', help="Liftoff GFF3 with extra_copy_number (optional)")
    parser.add_argument('--class-code', help="Comma-separated class codes (e.g. em,j)")

    # FASTA and DIAMOND options
    parser.add_argument('--ref-faa', help="Reference proteins FASTA")
    parser.add_argument('--qry-faa', help="Query proteins FASTA")
    parser.add_argument('--run-diamond', action='store_true')
    parser.add_argument('--run-bbh', action='store_true', help='Run bidirectional best hit analysis (requires --run-diamond)')
    parser.add_argument('--bbh-min-pident', type=float, default=30.0, help='Minimum pident for BBH analysis (default: 30.0)')
    parser.add_argument('--bbh-min-coverage', type=float, default=50.0, help='Minimum coverage for BBH analysis (default: 50.0)')
    parser.add_argument('--diamond-threads', type=int, default=40)

    # Pairwise alignment options (Biopython local alignment)
    parser.add_argument('--run-pairwise', action='store_true', help='Run Biopython pairwise alignment (adds pairwise_identity, pairwise_coverage_ref, pairwise_coverage_query, pairwise_aligned_length)')

    # Output options
    parser.add_argument('--output-prefix', default="synonym_mapping_liftover_gffcomp")
    parser.add_argument('--output-dir', default="pavprot_out", help="Output directory (default: pavprot_out)")

    # InterProScan options
    parser.add_argument('--interproscan-out', help="InterProScan TSV output file(s). Single file for single GFF, or comma-separated for 2 GFFs. Format: 'ref_interpro.tsv' or 'ref_interpro.tsv,query_interpro.tsv'")
    parser.add_argument('--run-interproscan', action='store_true', help='Run InterProScan on input protein files before parsing')
    parser.add_argument('--input-prots', help="Comma-separated protein FASTA file(s). Single file for single GFF, or 2 files for 2 GFFs. Format: 'ref.faa' or 'ref.faa,query.faa'")
    parser.add_argument('--interproscan-cpu', type=int, default=4, help='Number of CPUs for InterProScan (default: 4)')
    parser.add_argument('--interproscan-pathways', action='store_true', help='Include pathway annotations in InterProScan')
    parser.add_argument('--interproscan-databases', help='Databases to search (comma-separated, default: all)')

    # Output filtering options
    parser.add_argument('--filter-exact-match', action='store_true', help='Only output gene pairs with exact_match=1 (all transcripts are em)')
    parser.add_argument('--filter-exclusive-1to1', action='store_true', help='Only output exclusive 1:1 mappings (ref_multi_query=0 AND qry_multi_ref=0)')
    parser.add_argument('--filter-class-type-gene', help='Only output gene pairs with specified class_type_gene (comma-separated, e.g., "a,ackmnj")')

    return parser


def validate_inputs(args, parser: argparse.ArgumentParser) -> Tuple[List[str], List[str]]:
    """
    Validate all input files exist and return parsed file lists.

    Returns:
        Tuple of (ref_gff_list, interproscan_files)
    """
    # Validate tracking file
    if not os.path.exists(args.gff_comp):
        parser.error(f"Tracking file not found: {args.gff_comp}")

    # Validate GFF files
    if args.gff:
        for gff_file in args.gff.split(','):
            gff_file = gff_file.strip()
            if not os.path.exists(gff_file):
                parser.error(f"GFF file not found: {gff_file}")

    # Validate FASTA files
    if args.ref_faa and not os.path.exists(args.ref_faa):
        parser.error(f"Reference FASTA not found: {args.ref_faa}")
    if args.qry_faa and not os.path.exists(args.qry_faa):
        parser.error(f"Query FASTA not found: {args.qry_faa}")
    if args.liftoff_gff and not os.path.exists(args.liftoff_gff):
        parser.error(f"Liftoff GFF not found: {args.liftoff_gff}")

    # Parse GFF list
    ref_gff_list = [g.strip() for g in args.gff.split(',')] if args.gff else []
    num_gffs = len(ref_gff_list)

    # Handle InterProScan files
    interproscan_files = []
    if args.run_interproscan:
        interproscan_files = _run_interproscan_pipeline(args, parser, ref_gff_list, num_gffs)
    elif args.interproscan_out:
        interproscan_files = _validate_interproscan_files(args, parser, num_gffs)

    return ref_gff_list, interproscan_files


def _run_interproscan_pipeline(args, parser, ref_gff_list: List[str], num_gffs: int) -> List[str]:
    """Run InterProScan on input protein files."""
    if not args.input_prots:
        parser.error("--run-interproscan requires --input-prots argument")

    input_prot_files = [f.strip() for f in args.input_prots.split(',')]

    # Validate file counts match
    if args.gff:
        if num_gffs == 2 and len(input_prot_files) != 2:
            parser.error(f"When --gff has 2 files, --input-prots must also have exactly 2 comma-separated files. Got {len(input_prot_files)} protein files.")
        elif num_gffs == 1 and len(input_prot_files) > 2:
            parser.error(f"When --gff has 1 file, --input-prots can have at most 2 files. Got {len(input_prot_files)} protein files.")

        print(f"\nNote: Protein file order follows GFF file order:", file=sys.stderr)
        for i, (prot_file, gff_file) in enumerate(zip(input_prot_files, ref_gff_list)):
            file_type = "Reference" if i == 0 else "Query"
            print(f"  {file_type}: {prot_file} → {gff_file}", file=sys.stderr)
    else:
        print(f"\nNote: Running InterProScan without GFF - gene IDs will not be mapped", file=sys.stderr)

    # Validate files exist
    for f in input_prot_files:
        if not os.path.exists(f):
            parser.error(f"Protein file not found: {f}")

    # Run InterProScan
    print("\n" + "="*80, file=sys.stderr)
    print("RUNNING INTERPROSCAN", file=sys.stderr)
    print("="*80, file=sys.stderr)

    pavprot_out = os.path.join(os.getcwd(), args.output_dir)
    os.makedirs(pavprot_out, exist_ok=True)

    interproscan_output_files = []
    for i, prot_file in enumerate(input_prot_files):
        file_type = "Reference" if i == 0 else "Query"
        print(f"\n[{i+1}/{len(input_prot_files)}] Running InterProScan for {file_type} proteins: {prot_file}", file=sys.stderr)

        output_basename = Path(prot_file).stem + "_interproscan"
        output_base = os.path.join(pavprot_out, output_basename)

        success = run_interproscan(
            protein_file=prot_file,
            cpu=args.interproscan_cpu,
            output_base=output_base,
            output_format='TSV',
            pathways=args.interproscan_pathways,
            databases=args.interproscan_databases
        )

        if not success:
            print(f"Error: InterProScan failed for {prot_file}", file=sys.stderr)
            sys.exit(1)

        output_file = f"{output_base}.tsv"
        interproscan_output_files.append(output_file)
        print(f"  → InterProScan output: {output_file}", file=sys.stderr)

    print("\n" + "="*80, file=sys.stderr)
    print("✓ InterProScan completed for all files!", file=sys.stderr)
    print("="*80 + "\n", file=sys.stderr)

    return interproscan_output_files


def _validate_interproscan_files(args, parser, num_gffs: int) -> List[str]:
    """Validate existing InterProScan output files."""
    interproscan_files = [f.strip() for f in args.interproscan_out.split(',')]

    # Validate counts based on GFF configuration
    if num_gffs == 2:
        if len(interproscan_files) == 1:
            print(f"Note: Single InterProScan file provided with 2 GFFs - will be treated as reference-only", file=sys.stderr)
        elif len(interproscan_files) != 2:
            parser.error(f"--interproscan-out must have 1 or 2 comma-separated files when --gff has 2 GFFs. Got {len(interproscan_files)} files.")
    elif num_gffs == 1:
        if len(interproscan_files) == 1:
            print(f"Note: Single InterProScan file provided with 1 GFF - will be treated as reference-only", file=sys.stderr)
        elif len(interproscan_files) == 2:
            print(f"Note: Two InterProScan files provided with 1 GFF - first for reference (with gene mapping), second for query (protein-level only)", file=sys.stderr)
        elif len(interproscan_files) > 2:
            parser.error(f"--interproscan-out can have at most 2 files when --gff has 1 GFF. Got {len(interproscan_files)} files.")
    elif num_gffs == 0 and len(interproscan_files) > 0:
        print(f"Note: {len(interproscan_files)} InterProScan file(s) provided without GFF - protein-level data only (no gene mapping)", file=sys.stderr)

    # Validate files exist
    for f in interproscan_files:
        if not os.path.exists(f):
            parser.error(f"InterProScan file not found: {f}")

    return interproscan_files


def process_interproscan_integration(
    args,
    data: dict,
    interproscan_files: List[str],
    ref_gff_list: List[str],
    pavprot_out: str
) -> Tuple[dict, bool, dict, dict]:
    """
    Process InterProScan data and enrich the PAVprot data.

    Returns:
        Tuple of (enriched_data, has_interproscan, ref_interproscan_map, qry_interproscan_map)
    """
    num_gffs = len(ref_gff_list)
    ref_interproscan_map = {}
    qry_interproscan_map = {}
    has_interproscan = False

    if not interproscan_files or len(interproscan_files) == 0:
        return data, has_interproscan, ref_interproscan_map, qry_interproscan_map

    print("\n" + "="*80, file=sys.stderr)
    print("RUNNING INTERPROSCAN INTEGRATION (parse_interproscan functionality)", file=sys.stderr)
    print("="*80, file=sys.stderr)

    # Dispatch to appropriate handler based on configuration
    if num_gffs == 0:
        ref_interproscan_map, qry_interproscan_map = _process_interproscan_no_gff(
            interproscan_files, pavprot_out
        )
    elif num_gffs == 1 and len(interproscan_files) == 1:
        ref_interproscan_map, qry_interproscan_map = _process_interproscan_single_gff_single_file(
            data, interproscan_files, ref_gff_list, pavprot_out
        )
    elif num_gffs == 2 and len(interproscan_files) == 1:
        ref_interproscan_map, qry_interproscan_map = _process_interproscan_dual_gff_single_file(
            data, interproscan_files, ref_gff_list, pavprot_out
        )
    elif num_gffs == 1 and len(interproscan_files) == 2:
        ref_interproscan_map, qry_interproscan_map = _process_interproscan_single_gff_dual_file(
            interproscan_files, ref_gff_list, pavprot_out
        )
    elif num_gffs == 2 and len(interproscan_files) == 2:
        ref_interproscan_map, qry_interproscan_map = _process_interproscan_dual_gff_dual_file(
            interproscan_files, ref_gff_list, pavprot_out
        )

    # Enrich data with InterProScan information
    if qry_interproscan_map or ref_interproscan_map:
        has_interproscan = True
        print(f"\nEnriching PAVprot data with InterProScan totals...", file=sys.stderr)
        data = PAVprot.enrich_interproscan_data(data, qry_interproscan_map, ref_interproscan_map)
        print(f"  → Added columns: query_gene_total_iprdom_len, ref_gene_total_iprdom_len", file=sys.stderr)
        print(f"\n" + "="*80, file=sys.stderr)
        print(f"✓ InterProScan integration complete!", file=sys.stderr)
        print(f"  Query genes with IPR data: {len(qry_interproscan_map)}", file=sys.stderr)
        print(f"  Reference genes with IPR data: {len(ref_interproscan_map)}", file=sys.stderr)
        print("="*80 + "\n", file=sys.stderr)

    return data, has_interproscan, ref_interproscan_map, qry_interproscan_map


def _process_interproscan_no_gff(interproscan_files: List[str], pavprot_out: str) -> Tuple[dict, dict]:
    """Process InterProScan without GFF (protein-level only)."""
    print(f"\n[1/3] No GFF mode: Protein-level data only (no gene mapping)", file=sys.stderr)

    ref_interproscan_map = {}
    qry_interproscan_map = {}
    parsers_list = []

    for i, interpro_file in enumerate(interproscan_files):
        file_type = "Reference" if i == 0 else "Query"
        print(f"  {file_type} InterProScan: {interpro_file}", file=sys.stderr)

        parser = InterProParser(gff_file=None)
        df = parser.parse_tsv(interpro_file)
        print(f"  → Loaded {len(df)} InterProScan entries", file=sys.stderr)

        ipr_map = parser.total_ipr_length()
        print(f"  → Calculated for {len(ipr_map)} proteins", file=sys.stderr)

        if i == 0:
            ref_interproscan_map = ipr_map
        else:
            qry_interproscan_map = ipr_map

        parsers_list.append((parser, interpro_file))

    # Save outputs
    for i, (parser, interpro_file) in enumerate(parsers_list):
        file_type = "reference" if i == 0 else "query"
        file_base = Path(interpro_file).stem
        ipr_map = ref_interproscan_map if i == 0 else qry_interproscan_map
        _save_interproscan_outputs(parser, ipr_map, file_base, pavprot_out, has_gene_mapping=False)
        print(f"  → Saved {file_type} outputs to pavprot_out/", file=sys.stderr)

    print(f"\nNote: Gene IDs not added to output (no GFF provided)", file=sys.stderr)
    return ref_interproscan_map, qry_interproscan_map


def _process_interproscan_single_gff_single_file(
    data: dict, interproscan_files: List[str], ref_gff_list: List[str], pavprot_out: str
) -> Tuple[dict, dict]:
    """Process single InterProScan file with single GFF."""
    print(f"\n[1/4] Single GFF mode: Auto-detecting InterProScan type", file=sys.stderr)
    print(f"  GFF: {ref_gff_list[0]}", file=sys.stderr)
    print(f"  InterProScan: {interproscan_files[0]}", file=sys.stderr)

    interproscan_type = PAVprot.detect_interproscan_type(data, interproscan_files[0])

    parser = InterProParser(gff_file=ref_gff_list[0])
    df = parser.parse_tsv(interproscan_files[0])
    print(f"  → Loaded {len(df)} InterProScan entries", file=sys.stderr)

    ipr_map = parser.total_ipr_length()

    ref_interproscan_map = {}
    qry_interproscan_map = {}

    if interproscan_type == 'query':
        qry_interproscan_map = ipr_map
        print(f"  → Calculated for {len(qry_interproscan_map)} query genes", file=sys.stderr)
    else:
        ref_interproscan_map = ipr_map
        print(f"  → Calculated for {len(ref_interproscan_map)} reference genes", file=sys.stderr)

    file_base = Path(interproscan_files[0]).stem
    _save_interproscan_outputs(parser, ipr_map, file_base, pavprot_out, has_gene_mapping=bool(parser.transcript_to_gene_map))

    return ref_interproscan_map, qry_interproscan_map


def _process_interproscan_dual_gff_single_file(
    data: dict, interproscan_files: List[str], ref_gff_list: List[str], pavprot_out: str
) -> Tuple[dict, dict]:
    """Process single InterProScan file with dual GFFs."""
    print(f"\n[1/4] Dual GFF mode with single InterProScan: Auto-detecting type", file=sys.stderr)
    print(f"  Reference GFF: {ref_gff_list[0]}", file=sys.stderr)
    print(f"  Query GFF: {ref_gff_list[1]}", file=sys.stderr)
    print(f"  InterProScan: {interproscan_files[0]}", file=sys.stderr)

    interproscan_type = PAVprot.detect_interproscan_type(data, interproscan_files[0])
    gff_to_use = ref_gff_list[0] if interproscan_type == 'reference' else ref_gff_list[1]

    parser = InterProParser(gff_file=gff_to_use)
    df = parser.parse_tsv(interproscan_files[0])
    print(f"  → Loaded {len(df)} InterProScan entries", file=sys.stderr)

    ipr_map = parser.total_ipr_length()

    ref_interproscan_map = {}
    qry_interproscan_map = {}

    if interproscan_type == 'query':
        qry_interproscan_map = ipr_map
        print(f"  → Calculated for {len(qry_interproscan_map)} query genes", file=sys.stderr)
    else:
        ref_interproscan_map = ipr_map
        print(f"  → Calculated for {len(ref_interproscan_map)} reference genes", file=sys.stderr)

    file_base = Path(interproscan_files[0]).stem
    _save_interproscan_outputs(parser, ipr_map, file_base, pavprot_out, has_gene_mapping=bool(parser.transcript_to_gene_map))

    return ref_interproscan_map, qry_interproscan_map


def _process_interproscan_single_gff_dual_file(
    interproscan_files: List[str], ref_gff_list: List[str], pavprot_out: str
) -> Tuple[dict, dict]:
    """Process two InterProScan files with single GFF."""
    print(f"\n[1/4] Single GFF mode: Reference with gene mapping, Query without", file=sys.stderr)
    print(f"  Reference GFF: {ref_gff_list[0]}", file=sys.stderr)
    print(f"  Reference InterProScan: {interproscan_files[0]}", file=sys.stderr)
    print(f"  Query InterProScan: {interproscan_files[1]} (no gene mapping)", file=sys.stderr)

    # Reference with GFF mapping
    ref_parser = InterProParser(gff_file=ref_gff_list[0])
    ref_df = ref_parser.parse_tsv(interproscan_files[0])
    print(f"  → Loaded {len(ref_df)} reference InterProScan entries", file=sys.stderr)
    ref_interproscan_map = ref_parser.total_ipr_length()
    print(f"  → Calculated for {len(ref_interproscan_map)} reference genes", file=sys.stderr)

    # Query without GFF mapping
    qry_parser = InterProParser(gff_file=None)
    qry_df = qry_parser.parse_tsv(interproscan_files[1])
    print(f"  → Loaded {len(qry_df)} query InterProScan entries", file=sys.stderr)
    qry_interproscan_map = qry_parser.total_ipr_length()
    print(f"  → Calculated for {len(qry_interproscan_map)} query proteins", file=sys.stderr)

    # Save outputs
    ref_base = Path(interproscan_files[0]).stem
    qry_base = Path(interproscan_files[1]).stem
    _save_interproscan_outputs(ref_parser, ref_interproscan_map, ref_base, pavprot_out, has_gene_mapping=bool(ref_parser.transcript_to_gene_map))
    _save_interproscan_outputs(qry_parser, qry_interproscan_map, qry_base, pavprot_out, has_gene_mapping=False)

    return ref_interproscan_map, qry_interproscan_map


def _process_interproscan_dual_gff_dual_file(
    interproscan_files: List[str], ref_gff_list: List[str], pavprot_out: str
) -> Tuple[dict, dict]:
    """Process two InterProScan files with two GFFs."""
    print(f"\n[1/4] Dual GFF mode: Reference + Query", file=sys.stderr)
    print(f"  Reference GFF: {ref_gff_list[0]}", file=sys.stderr)
    print(f"  Reference InterProScan: {interproscan_files[0]}", file=sys.stderr)
    print(f"  Query GFF: {ref_gff_list[1]}", file=sys.stderr)
    print(f"  Query InterProScan: {interproscan_files[1]}", file=sys.stderr)

    # Reference
    ref_parser = InterProParser(gff_file=ref_gff_list[0])
    ref_df = ref_parser.parse_tsv(interproscan_files[0])
    print(f"  → Loaded {len(ref_df)} reference InterProScan entries", file=sys.stderr)
    ref_interproscan_map = ref_parser.total_ipr_length()
    print(f"  → Calculated for {len(ref_interproscan_map)} reference genes", file=sys.stderr)

    # Query
    qry_parser = InterProParser(gff_file=ref_gff_list[1])
    qry_df = qry_parser.parse_tsv(interproscan_files[1])
    print(f"  → Loaded {len(qry_df)} query InterProScan entries", file=sys.stderr)
    qry_interproscan_map = qry_parser.total_ipr_length()
    print(f"  → Calculated for {len(qry_interproscan_map)} query genes", file=sys.stderr)

    # Save outputs
    ref_base = Path(interproscan_files[0]).stem
    qry_base = Path(interproscan_files[1]).stem
    _save_interproscan_outputs(ref_parser, ref_interproscan_map, ref_base, pavprot_out, has_gene_mapping=bool(ref_parser.transcript_to_gene_map))
    _save_interproscan_outputs(qry_parser, qry_interproscan_map, qry_base, pavprot_out, has_gene_mapping=bool(qry_parser.transcript_to_gene_map))

    return ref_interproscan_map, qry_interproscan_map


def _save_interproscan_outputs(
    parser: 'InterProParser',
    ipr_map: dict,
    file_base: str,
    pavprot_out: str,
    has_gene_mapping: bool
) -> None:
    """Save InterProScan analysis outputs to files."""
    total_ipr_file = os.path.join(pavprot_out, f"{file_base}_total_ipr_length.tsv")
    domain_dist_file = os.path.join(pavprot_out, f"{file_base}_domain_distribution.tsv")

    # Save total IPR lengths
    id_col = 'gene_id' if has_gene_mapping else 'protein_accession'
    total_df = pd.DataFrame(list(ipr_map.items()), columns=[id_col, 'total_iprdom_len'])
    total_df.to_csv(total_ipr_file, sep='\t', index=False)

    # Save domain distribution
    domain_stats = parser.domain_distribution()
    if len(domain_stats) > 0:
        domain_stats.to_csv(domain_dist_file, sep='\t', index=False, na_rep='')


def write_results(
    args,
    data: dict,
    has_interproscan: bool,
    has_bbh: bool,
    has_pairwise: bool,
    interproscan_files: List[str],
    filter_set: Optional[Set[str]]
) -> str:
    """
    Write final results to output file.

    Returns:
        Path to the output file.
    """
    pavprot_out = os.path.join(os.getcwd(), args.output_dir)
    os.makedirs(pavprot_out, exist_ok=True)

    # Build output filename
    output_file = _build_output_filename(args, interproscan_files, filter_set, pavprot_out)

    # Build header
    header = _build_header(args, has_interproscan, has_bbh, has_pairwise)

    # Parse filter options
    filter_class_types = None
    if args.filter_class_type_gene:
        filter_class_types = {ct.strip() for ct in args.filter_class_type_gene.split(',')}

    # Write output
    filtered_count, total_count = _write_output_file(
        output_file, header, data, args, has_interproscan, has_bbh, has_pairwise, filter_class_types
    )

    # Report filtering stats
    if filtered_count > 0:
        print(f"Filtered {filtered_count} of {total_count} entries ({total_count - filtered_count} remaining)", file=sys.stderr)
    print(f"Results saved to {output_file}", file=sys.stderr)

    return output_file


def _build_output_filename(
    args,
    interproscan_files: List[str],
    filter_set: Optional[Set[str]],
    pavprot_out: str
) -> str:
    """Build the output filename based on configuration."""
    # Add InterProScan basename prefix when single file is provided
    interproscan_prefix = ""
    if interproscan_files and len(interproscan_files) == 1:
        interpro_basename = Path(interproscan_files[0]).stem
        interproscan_prefix = interpro_basename.replace('.prot', '').replace('.faa', '')

    # Build base prefix
    base_prefix = "synonym_mapping_liftover_gffcomp"
    if args.output_prefix and args.output_prefix != "synonym_mapping_liftover_gffcomp":
        full_prefix = f"{base_prefix}_{args.output_prefix}"
    else:
        full_prefix = base_prefix

    # Prepend InterProScan prefix
    if interproscan_prefix:
        full_prefix = f"{interproscan_prefix}_{full_prefix}"

    # Add suffix
    suffix = "_diamond_blastp.tsv" if args.run_diamond else ".tsv"

    if filter_set:
        safe_codes = "_".join(sorted(filter_set))
        return os.path.join(pavprot_out, f"{full_prefix}_{safe_codes}{suffix}")
    else:
        return os.path.join(pavprot_out, f"{full_prefix}{suffix}")


def _build_header(args, has_interproscan: bool, has_bbh: bool, has_pairwise: bool = False) -> str:
    """Build the output file header."""
    header = "ref_gene\tref_transcript\tquery_gene\tquery_transcript\tclass_code\texons\tclass_code_multi_query\tclass_code_multi_ref\tclass_type_transcript\tclass_type_gene\temckmnj\temckmnje\tref_multi_transcript\tqry_multi_transcript\texact_match\tclass_code_pair\tref_multi_query\tqry_multi_ref\tref_query_count\tqry_ref_count"

    if args.run_diamond:
        header += "\tpident\tqcovhsp\tscovhsp\tidentical_aa\tmismatched_aa\tindels_aa\taligned_aa"
    if has_bbh:
        header += "\tis_bbh\tbbh_avg_pident\tbbh_avg_coverage"
    if has_pairwise:
        header += "\tpairwise_identity\tpairwise_coverage_ref\tpairwise_coverage_query\tpairwise_aligned_length"
    if args.liftoff_gff:
        header += "\textra_copy_number"
    if has_interproscan:
        header += "\tquery_total_ipr_domain_length\tref_total_ipr_domain_length"

    return header


def _write_output_file(
    output_file: str,
    header: str,
    data: dict,
    args,
    has_interproscan: bool,
    has_bbh: bool,
    has_pairwise: bool,
    filter_class_types: Optional[Set[str]]
) -> Tuple[int, int]:
    """Write the output file and return filter statistics."""
    filtered_count = 0
    total_count = 0

    with open(output_file, 'w') as f:
        f.write(header + "\n")
        for entries in data.values():
            for e in entries:
                total_count += 1

                # Apply filters
                if args.filter_exact_match and e.get('exact_match', 0) != 1:
                    filtered_count += 1
                    continue
                if args.filter_exclusive_1to1 and (e.get('ref_multi_query', 0) != 0 or e.get('qry_multi_ref', 0) != 0):
                    filtered_count += 1
                    continue
                if filter_class_types and e.get('class_type_gene', 'pru') not in filter_class_types:
                    filtered_count += 1
                    continue

                # Build output line
                exons = e.get('exons') if e.get('exons') is not None else '-'
                base = f"{e['ref_gene']}\t{e['ref_transcript']}\t{e['query_gene']}\t{e['query_transcript']}\t{e['class_code']}\t{exons}\t{e['class_code_multi_query']}\t{e['class_code_multi_ref']}\t{e['class_type_transcript']}\t{e['class_type_gene']}\t{e['ackmnj']}\t{e['ackmnje']}\t{e['ref_multi_transcript']}\t{e['qry_multi_transcript']}\t{e['exact_match']}\t{e['class_code_pair']}\t{e['ref_multi_query']}\t{e['qry_multi_ref']}\t{e['ref_query_count']}\t{e['qry_ref_count']}"

                diamond_line = ""
                if args.run_diamond:
                    pident = e.get('pident', 0)
                    qcovhsp = e.get('qcovhsp', 0)
                    scovhsp = e.get('scovhsp', 0)
                    diamond_line = f"\t{pident:.1f}\t{qcovhsp:.1f}\t{scovhsp:.1f}\t{e.get('identical_aa', 0)}\t{e.get('mismatched_aa', 0)}\t{e.get('indels_aa', 0)}\t{e.get('aligned_aa', 0)}"

                bbh_line = ""
                if has_bbh:
                    is_bbh = e.get('is_bbh', 0)
                    bbh_avg_pident = e.get('bbh_avg_pident')
                    bbh_avg_coverage = e.get('bbh_avg_coverage')
                    bbh_avg_pident_str = f"{bbh_avg_pident:.1f}" if bbh_avg_pident is not None else 'NA'
                    bbh_avg_coverage_str = f"{bbh_avg_coverage:.1f}" if bbh_avg_coverage is not None else 'NA'
                    bbh_line = f"\t{is_bbh}\t{bbh_avg_pident_str}\t{bbh_avg_coverage_str}"

                pairwise_line = ""
                if has_pairwise:
                    pw_identity = e.get('pairwise_identity')
                    pw_cov_ref = e.get('pairwise_coverage_ref')
                    pw_cov_query = e.get('pairwise_coverage_query')
                    pw_aligned_len = e.get('pairwise_aligned_length')
                    pw_identity_str = f"{pw_identity:.2f}" if pw_identity is not None else 'NA'
                    pw_cov_ref_str = f"{pw_cov_ref:.2f}" if pw_cov_ref is not None else 'NA'
                    pw_cov_query_str = f"{pw_cov_query:.2f}" if pw_cov_query is not None else 'NA'
                    pw_aligned_len_str = str(pw_aligned_len) if pw_aligned_len is not None else 'NA'
                    pairwise_line = f"\t{pw_identity_str}\t{pw_cov_ref_str}\t{pw_cov_query_str}\t{pw_aligned_len_str}"

                extra_copy_line = ""
                if args.liftoff_gff:
                    extra_copy_line = f"\t{e.get('extra_copy_number', 0)}"

                interproscan_line = ""
                if has_interproscan:
                    query_val = e.get('query_gene_total_iprdom_len', 0)
                    ref_val = e.get('ref_gene_total_iprdom_len', 0)
                    query_val = 'NA' if query_val == 0 else query_val
                    ref_val = 'NA' if ref_val == 0 else ref_val
                    interproscan_line = f"\t{query_val}\t{ref_val}"

                f.write(f"{base}{diamond_line}{bbh_line}{pairwise_line}{extra_copy_line}{interproscan_line}\n")

    return filtered_count, total_count


# =============================================================================
# Gene-Level Aggregation and Scenario Integration
# =============================================================================

def aggregate_to_gene_level(
    transcript_level_file: str,
    output_dir: str,
    ref_faa: Optional[str] = None,
    qry_faa: Optional[str] = None,
    ref_gff: Optional[str] = None,
    query_gff: Optional[str] = None
) -> str:
    """
    Aggregate transcript-level output to gene-level and add scenario columns.

    Creates a gene-level output where:
    - Each row is a unique ref_gene:query_gene pair
    - Transcripts are comma-separated in ref_transcripts and query_transcripts columns
    - scenario and mapping_type columns are added based on exclusive scenario detection

    Args:
        transcript_level_file: Path to transcript-level TSV output
        output_dir: Output directory
        ref_faa: Path to reference protein FASTA (for unmapped detection)
        qry_faa: Path to query protein FASTA (for unmapped detection)
        ref_gff: Path to reference GFF3 (for unmapped detection)
        query_gff: Path to query GFF3 (for unmapped detection)

    Returns:
        Path to the gene-level output file
    """
    print(f"\n{'='*60}", file=sys.stderr)
    print("Aggregating to gene-level with scenario detection", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)

    # Read transcript-level output
    print(f"Reading transcript-level output: {transcript_level_file}", file=sys.stderr)
    df = pd.read_csv(transcript_level_file, sep='\t')
    print(f"  Loaded {len(df)} transcript-level entries", file=sys.stderr)

    # =========================================================================
    # Step 1: Aggregate to gene-level
    # =========================================================================
    print(f"\nAggregating to gene-level...", file=sys.stderr)

    # Define aggregation rules for each column
    def agg_first(x):
        return x.iloc[0]

    def agg_comma_join(x):
        return ','.join(sorted(set(str(v) for v in x if pd.notna(v))))

    def agg_max(x):
        return x.max()

    def agg_mean(x):
        vals = x.dropna()
        return vals.mean() if len(vals) > 0 else None

    # Group by gene pair
    gene_pairs = df.groupby(['ref_gene', 'query_gene']).agg({
        'ref_transcript': agg_comma_join,
        'query_transcript': agg_comma_join,
        'class_code': agg_comma_join,  # Combine all class codes
        'exons': agg_first,
        'class_code_multi_query': agg_first,
        'class_code_multi_ref': agg_first,
        'class_type_transcript': agg_comma_join,
        'class_type_gene': agg_first,
        'emckmnj': agg_first,
        'emckmnje': agg_first,
        'ref_multi_transcript': agg_max,
        'qry_multi_transcript': agg_max,
        'exact_match': agg_max,
        'class_code_pair': agg_first,
        'ref_multi_query': agg_first,
        'qry_multi_ref': agg_first,
        'ref_query_count': agg_first,
        'qry_ref_count': agg_first,
    }).reset_index()

    # Rename transcript columns
    gene_pairs = gene_pairs.rename(columns={
        'ref_transcript': 'ref_transcripts',
        'query_transcript': 'query_transcripts'
    })

    # Add transcript counts
    gene_pairs['ref_transcript_count'] = gene_pairs['ref_transcripts'].apply(
        lambda x: len(x.split(',')) if x else 0
    )
    gene_pairs['query_transcript_count'] = gene_pairs['query_transcripts'].apply(
        lambda x: len(x.split(',')) if x else 0
    )

    # Handle optional columns if present
    optional_cols = ['pident', 'qcovhsp', 'scovhsp', 'is_bbh', 'bbh_avg_pident',
                     'bbh_avg_coverage', 'pairwise_identity', 'pairwise_coverage_ref',
                     'pairwise_coverage_query', 'pairwise_aligned_length',
                     'query_total_ipr_domain_length', 'ref_total_ipr_domain_length',
                     'extra_copy_number']

    for col in optional_cols:
        if col in df.columns:
            gene_agg = df.groupby(['ref_gene', 'query_gene'])[col].agg(agg_mean).reset_index()
            gene_pairs = gene_pairs.merge(gene_agg, on=['ref_gene', 'query_gene'], how='left')

    print(f"  Created {len(gene_pairs)} gene-level pairs", file=sys.stderr)

    # =========================================================================
    # Step 2: Detect scenarios (exclusive)
    # =========================================================================
    print(f"\nDetecting exclusive scenarios...", file=sys.stderr)

    # Get CDI genes first (for exclusivity)
    cdi_ref_genes, cdi_query_genes = get_cdi_genes(gene_pairs)
    print(f"  CDI genes: {len(cdi_ref_genes)} ref, {len(cdi_query_genes)} query", file=sys.stderr)

    # Initialize scenario columns
    gene_pairs['scenario'] = ''
    gene_pairs['mapping_type'] = ''

    # Detect E (1:1)
    ref_counts = gene_pairs.groupby('ref_gene')['query_gene'].nunique()
    query_counts = gene_pairs.groupby('query_gene')['ref_gene'].nunique()
    refs_1to1 = set(ref_counts[ref_counts == 1].index)
    queries_1to1 = set(query_counts[query_counts == 1].index)

    mask_E = (gene_pairs['ref_gene'].isin(refs_1to1)) & (gene_pairs['query_gene'].isin(queries_1to1))
    gene_pairs.loc[mask_E, 'scenario'] = 'E'
    gene_pairs.loc[mask_E, 'mapping_type'] = '1to1'
    print(f"  E (1to1): {mask_E.sum()} pairs", file=sys.stderr)

    # Detect A (1to2N, exactly 2 queries, NOT in CDI)
    refs_1to2N = set(ref_counts[ref_counts == 2].index) - cdi_ref_genes
    mask_A = (gene_pairs['ref_gene'].isin(refs_1to2N)) & (gene_pairs['scenario'] == '')
    gene_pairs.loc[mask_A, 'scenario'] = 'A'
    gene_pairs.loc[mask_A, 'mapping_type'] = '1to2N'
    print(f"  A (1to2N): {mask_A.sum()} pairs", file=sys.stderr)

    # Detect J (1to2N+, 3+ queries, NOT in CDI)
    refs_1to2Nplus = set(ref_counts[ref_counts >= 3].index) - cdi_ref_genes
    mask_J = (gene_pairs['ref_gene'].isin(refs_1to2Nplus)) & (gene_pairs['scenario'] == '')
    gene_pairs.loc[mask_J, 'scenario'] = 'J'
    gene_pairs.loc[mask_J, 'mapping_type'] = '1to2N+'
    print(f"  J (1to2N+): {mask_J.sum()} pairs", file=sys.stderr)

    # Detect B (Nto1, NOT in CDI)
    queries_Nto1 = set(query_counts[query_counts > 1].index) - cdi_query_genes
    mask_B = (gene_pairs['query_gene'].isin(queries_Nto1)) & (gene_pairs['scenario'] == '')
    gene_pairs.loc[mask_B, 'scenario'] = 'B'
    gene_pairs.loc[mask_B, 'mapping_type'] = 'Nto1'
    print(f"  B (Nto1): {mask_B.sum()} pairs", file=sys.stderr)

    # Detect CDI (remaining pairs with multi-mapping on both sides)
    mask_CDI = (gene_pairs['ref_gene'].isin(cdi_ref_genes)) & (gene_pairs['query_gene'].isin(cdi_query_genes))
    gene_pairs.loc[mask_CDI & (gene_pairs['scenario'] == ''), 'scenario'] = 'CDI'
    gene_pairs.loc[mask_CDI & (gene_pairs['mapping_type'] == ''), 'mapping_type'] = 'complex'
    print(f"  CDI (complex): {(gene_pairs['scenario'] == 'CDI').sum()} pairs", file=sys.stderr)

    # =========================================================================
    # Step 3: Write gene-level output
    # =========================================================================
    output_basename = Path(transcript_level_file).stem
    gene_level_file = os.path.join(output_dir, f"{output_basename}_gene_level.tsv")

    # Reorder columns to put scenario and mapping_type early
    cols = gene_pairs.columns.tolist()
    priority_cols = ['ref_gene', 'ref_transcripts', 'ref_transcript_count',
                     'query_gene', 'query_transcripts', 'query_transcript_count',
                     'scenario', 'mapping_type']
    other_cols = [c for c in cols if c not in priority_cols]
    gene_pairs = gene_pairs[priority_cols + other_cols]

    gene_pairs.to_csv(gene_level_file, sep='\t', index=False)
    print(f"\nGene-level output: {gene_level_file}", file=sys.stderr)
    print(f"  Total gene pairs: {len(gene_pairs)}", file=sys.stderr)

    # Print scenario summary
    print(f"\nScenario summary:", file=sys.stderr)
    scenario_counts = gene_pairs['scenario'].value_counts()
    for scenario, count in scenario_counts.items():
        if scenario:
            print(f"  {scenario}: {count}", file=sys.stderr)

    return gene_level_file


def main():
    """Main entry point for PAVprot pipeline."""
    # =========================================================================
    # Step 1: Parse arguments and validate inputs
    # =========================================================================
    parser = create_argument_parser()
    args = parser.parse_args()

    # Validate inputs and get file lists
    ref_gff_list, interproscan_files = validate_inputs(args, parser)

    # =========================================================================
    # Step 2: Parse tracking file and apply class code filter
    # =========================================================================
    ref_gff_for_tracking = ref_gff_list[0] if ref_gff_list else None
    filter_set = {c.strip() for c in args.class_code.split(',')} if args.class_code else None
    full, filtered = PAVprot.parse_tracking(args.gff_comp, ref_gff_for_tracking, filter_set)
    data = filtered if filtered else full

    # =========================================================================
    # Step 3: Run DIAMOND BLASTP if requested
    # =========================================================================
    has_bbh = False
    if args.run_diamond:
        if not args.ref_faa or not args.qry_faa:
            print("Error: --run-diamond requires --ref-faa and --qry-faa", file=sys.stderr)
            sys.exit(1)

        pavprot_out = os.path.join(os.getcwd(), args.output_dir)
        compareprot_out = os.path.join(pavprot_out, 'compareprot_out')
        input_seq_dir = os.path.join(compareprot_out, 'input_seq_dir')
        os.makedirs(input_seq_dir, exist_ok=True)

        ref_faa_path = os.path.join(input_seq_dir, "ref_all.faa")
        qry_faa_path = os.path.join(input_seq_dir, "qry_all.faa")

        with open(ref_faa_path, 'w') as f:
            for h, s in PAVprot.fasta2dict(args.ref_faa, is_query=False):
                f.write(f">{h}\n{s}\n")
        with open(qry_faa_path, 'w') as f:
            for h, s in PAVprot.fasta2dict(args.qry_faa, is_query=True):
                f.write(f">{h}\n{s}\n")

        diamond = DiamondRunner(threads=args.diamond_threads, output_prefix=args.output_prefix, output_dir=args.output_dir)

        if args.run_bbh:
            # Run bidirectional DIAMOND for BBH analysis
            fwd_diamond, rev_diamond = diamond.run_bidirectional(ref_faa_path, qry_faa_path)
            data = diamond.enrich_blastp(data, fwd_diamond)

            # Run BBH analysis
            print(f"\nRunning Bidirectional Best Hit analysis...", file=sys.stderr)
            bbh_analyzer = BidirectionalBestHits()
            bbh_analyzer.load_forward(fwd_diamond)
            bbh_analyzer.load_reverse(rev_diamond)
            bbh_df = bbh_analyzer.find_bbh(
                min_pident=args.bbh_min_pident,
                min_coverage=args.bbh_min_coverage
            )

            # Save BBH results
            bbh_output = os.path.join(compareprot_out, f"{args.output_prefix}_bbh_results.tsv")
            if not bbh_df.empty:
                bbh_analyzer.save_results(bbh_output)
                has_bbh = True

                # Enrich pavprot data with BBH info
                data = enrich_pavprot_with_bbh(data, bbh_df)
            else:
                print("  Warning: No BBH pairs found", file=sys.stderr)
        else:
            # Run forward-only DIAMOND (original behavior)
            diamond_tsv_gz = diamond.diamond_blastp(ref_faa_path, qry_faa_path)
            data = diamond.enrich_blastp(data, diamond_tsv_gz)

    # =========================================================================
    # Step 4: Compute all metrics in a single pass
    # =========================================================================
    data = PAVprot.compute_all_metrics(data)

    # Apply extra copy number from Liftoff GFF
    if args.liftoff_gff:
        data = PAVprot.filter_extra_copy_transcripts(data, args.liftoff_gff)

    # =========================================================================
    # Step 5: Process InterProScan integration
    # =========================================================================
    pavprot_out = os.path.join(os.getcwd(), args.output_dir)
    os.makedirs(pavprot_out, exist_ok=True)

    data, has_interproscan, _, _ = process_interproscan_integration(
        args, data, interproscan_files, ref_gff_list, pavprot_out
    )

    # =========================================================================
    # Step 5b: Run Biopython pairwise alignment if requested
    # =========================================================================
    has_pairwise = False
    if args.run_pairwise:
        if not args.ref_faa or not args.qry_faa:
            print("Error: --run-pairwise requires --ref-faa and --qry-faa", file=sys.stderr)
            sys.exit(1)

        print(f"\nRunning Biopython pairwise alignment...", file=sys.stderr)
        data = enrich_pairwise_alignment(data, args.ref_faa, args.qry_faa)
        has_pairwise = True

    # =========================================================================
    # Step 6: Write results
    # =========================================================================
    output_file = write_results(args, data, has_interproscan, has_bbh, has_pairwise, interproscan_files, filter_set)

    # =========================================================================
    # Step 7: Run one-to-many mapping detection
    # =========================================================================
    print(f"\nDetecting one-to-many and many-to-one gene mappings...", file=sys.stderr)
    try:
        output_basename = Path(output_file).stem
        detect_multiple_mappings(output_file, output_prefix=output_basename)
    except Exception as e:
        print(f"Warning: One-to-many mapping detection failed: {e}", file=sys.stderr)

    # =========================================================================
    # Step 8: Gene-level aggregation with scenario detection
    # =========================================================================
    pavprot_out = os.path.join(os.getcwd(), args.output_dir)

    # Get GFF files for unmapped gene detection
    ref_gff, query_gff = None, None
    if args.gff:
        gff_files = [f.strip() for f in args.gff.split(',')]
        if len(gff_files) >= 1:
            ref_gff = gff_files[0]
        if len(gff_files) >= 2:
            query_gff = gff_files[1]

    try:
        gene_level_file = aggregate_to_gene_level(
            transcript_level_file=output_file,
            output_dir=pavprot_out,
            ref_faa=args.ref_faa,
            qry_faa=args.qry_faa,
            ref_gff=ref_gff,
            query_gff=query_gff
        )
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"Pipeline complete!", file=sys.stderr)
        print(f"  Transcript-level: {output_file}", file=sys.stderr)
        print(f"  Gene-level:       {gene_level_file}", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Gene-level aggregation failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()