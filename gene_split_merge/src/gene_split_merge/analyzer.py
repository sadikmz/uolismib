#!/usr/bin/env python3
"""
Gene Structure Change Analyzer
===============================
Detects gene splits and merges between two genome assemblies of the same individual.

Author: Bioinformatics Workflow
Date: 2025-12-06
"""

import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict, Tuple, Set
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Gene:
    """Represents a gene with its genomic coordinates and metadata."""
    gene_id: str
    chromosome: str
    start: int
    end: int
    strand: str
    protein_seq: str = ""
    
    @property
    def length(self) -> int:
        """Returns gene length in base pairs."""
        return self.end - self.start + 1
    
    @property
    def midpoint(self) -> int:
        """Returns midpoint coordinate of the gene."""
        return (self.start + self.end) // 2


@dataclass
class BlastHit:
    """Represents a BLAST alignment hit."""
    query_id: str
    subject_id: str
    pident: float  # Percent identity
    length: int  # Alignment length
    qstart: int
    qend: int
    qlen: int  # Query length
    sstart: int
    send: int
    slen: int  # Subject length
    evalue: float
    bitscore: float
    
    @property
    def query_coverage(self) -> float:
        """Calculate query coverage percentage."""
        return (self.length / self.qlen) * 100
    
    @property
    def subject_coverage(self) -> float:
        """Calculate subject coverage percentage."""
        return (self.length / self.slen) * 100


@dataclass
class GeneRelationship:
    """Represents a detected gene split or merge relationship."""
    relationship_type: str  # 'split' or 'merge'
    ref_genes: List[str]
    updated_genes: List[str]
    confidence_score: float
    evidence: Dict[str, any]


class GFFParser:
    """Parse GFF3 files and extract gene information."""
    
    @staticmethod
    def parse_gff(gff_file: str) -> Dict[str, Gene]:
        """
        Parse GFF3 file and return dictionary of genes.
        
        Args:
            gff_file: Path to GFF3 file
            
        Returns:
            Dictionary mapping gene_id to Gene objects
        """
        genes = {}
        
        logger.info(f"Parsing GFF file: {gff_file}")
        
        with open(gff_file, 'r') as f:
            for line in f:
                if line.startswith('#'):
                    continue
                    
                parts = line.strip().split('\t')
                if len(parts) < 9:
                    continue
                
                feature_type = parts[2]
                
                # We want gene features (handles both 'gene' and 'protein_coding_gene')
                if feature_type not in ['gene', 'protein_coding_gene']:
                    continue
                
                chrom = parts[0]
                start = int(parts[3])
                end = int(parts[4])
                strand = parts[6]
                attributes = parts[8]
                
                # Extract gene ID from attributes
                gene_id = None
                for attr in attributes.split(';'):
                    if attr.startswith('ID='):
                        gene_id = attr.split('=')[1]
                        break
                
                if gene_id:
                    genes[gene_id] = Gene(
                        gene_id=gene_id,
                        chromosome=chrom,
                        start=start,
                        end=end,
                        strand=strand
                    )
        
        logger.info(f"Parsed {len(genes)} genes from {gff_file}")
        return genes

    @staticmethod
    def build_transcript_to_gene_map(gff_file: str) -> Dict[str, str]:
        """
        Build mapping from transcript/mRNA IDs to gene IDs from GFF.
        This handles cases where protein IDs correspond to transcript IDs.

        Args:
            gff_file: Path to GFF3 file

        Returns:
            Dictionary mapping transcript_id to gene_id
        """
        mapping = {}

        logger.info(f"Building transcript-to-gene mapping from: {gff_file}")

        with open(gff_file, 'r') as f:
            for line in f:
                if line.startswith('#'):
                    continue

                parts = line.strip().split('\t')
                if len(parts) < 9:
                    continue

                feature_type = parts[2]

                # Look for mRNA/transcript features
                if feature_type not in ['mRNA', 'transcript']:
                    continue

                attributes = parts[8]
                transcript_id = None
                gene_id = None

                # Extract transcript ID and parent gene ID
                for attr in attributes.split(';'):
                    if attr.startswith('ID='):
                        transcript_id = attr.split('=')[1]
                    elif attr.startswith('Parent='):
                        gene_id = attr.split('=')[1]

                if transcript_id and gene_id:
                    mapping[transcript_id] = gene_id

        logger.info(f"Built mapping for {len(mapping)} transcripts")
        return mapping

    @staticmethod
    def get_protein_lengths_by_transcript(genes: Dict[str, Gene],
                                         transcript_map: Dict[str, str]) -> Dict[str, int]:
        """
        Build protein length dictionary using transcript IDs as keys.
        This is needed because BLAST results use transcript IDs, not gene IDs.

        Args:
            genes: Dictionary of Gene objects
            transcript_map: Mapping from transcript IDs to gene IDs

        Returns:
            Dictionary mapping transcript_id to protein length
        """
        lengths = {}
        for transcript_id, gene_id in transcript_map.items():
            if gene_id in genes and genes[gene_id].protein_seq:
                lengths[transcript_id] = len(genes[gene_id].protein_seq)

        logger.info(f"Built protein lengths for {len(lengths)} transcripts")
        return lengths

    @staticmethod
    def add_protein_sequences(genes: Dict[str, Gene], fasta_file: str,
                             transcript_map: Dict[str, str] = None) -> None:
        """
        Add protein sequences to Gene objects from FASTA file.
        Handles both direct gene IDs and transcript IDs using the provided mapping.

        Args:
            genes: Dictionary of Gene objects
            fasta_file: Path to protein FASTA file
            transcript_map: Optional mapping from transcript IDs to gene IDs
        """
        from Bio import SeqIO

        logger.info(f"Loading protein sequences from: {fasta_file}")

        seq_count = 0
        for record in SeqIO.parse(fasta_file, 'fasta'):
            protein_id = record.id
            gene_id = None

            # Strategy 1: Try exact match with gene ID
            if protein_id in genes:
                gene_id = protein_id
            # Strategy 2: Use transcript-to-gene mapping if provided
            elif transcript_map and protein_id in transcript_map:
                gene_id = transcript_map[protein_id]
            # Strategy 3: Try protein ID without -p suffix (e.g., GENE-t36_1-p1 -> GENE-t36_1)
            elif '-p' in protein_id:
                base_id = protein_id.rsplit('-p', 1)[0]
                if base_id in genes:
                    gene_id = base_id
                elif transcript_map and base_id in transcript_map:
                    gene_id = transcript_map[base_id]

            if gene_id and gene_id in genes:
                genes[gene_id].protein_seq = str(record.seq)
                seq_count += 1

        logger.info(f"Added protein sequences for {seq_count} genes")


class BlastAnalyzer:
    """Analyze BLAST results to find gene relationships."""
    
    @staticmethod
    def parse_blast_outfmt6(blast_file: str, query_lens: Dict[str, int], 
                           subject_lens: Dict[str, int]) -> List[BlastHit]:
        """
        Parse BLAST output in outfmt 6 format.
        
        Args:
            blast_file: Path to BLAST output file
            query_lens: Dictionary of query sequence lengths
            subject_lens: Dictionary of subject sequence lengths
            
        Returns:
            List of BlastHit objects
        """
        hits = []
        
        logger.info(f"Parsing BLAST results: {blast_file}")
        
        with open(blast_file, 'r') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) < 12:
                    continue
                
                query_id = parts[0]
                subject_id = parts[1]
                
                hit = BlastHit(
                    query_id=query_id,
                    subject_id=subject_id,
                    pident=float(parts[2]),
                    length=int(parts[3]),
                    qstart=int(parts[6]),
                    qend=int(parts[7]),
                    qlen=query_lens.get(query_id, 0),
                    sstart=int(parts[8]),
                    send=int(parts[9]),
                    slen=subject_lens.get(subject_id, 0),
                    evalue=float(parts[10]),
                    bitscore=float(parts[11])
                )
                hits.append(hit)
        
        logger.info(f"Parsed {len(hits)} BLAST hits")
        return hits
    
    @staticmethod
    def filter_hits(hits: List[BlastHit], min_identity: float = 80.0,
                   min_coverage: float = 70.0, max_evalue: float = 1e-10) -> List[BlastHit]:
        """
        Filter BLAST hits based on quality thresholds.
        
        Args:
            hits: List of BlastHit objects
            min_identity: Minimum percent identity
            min_coverage: Minimum query coverage percentage
            max_evalue: Maximum e-value threshold
            
        Returns:
            Filtered list of BlastHit objects
        """
        filtered = [
            hit for hit in hits
            if (hit.pident >= min_identity and
                hit.query_coverage >= min_coverage and
                hit.evalue <= max_evalue)
        ]
        
        logger.info(f"Filtered {len(hits)} hits to {len(filtered)} high-quality hits")
        return filtered
    
    @staticmethod
    def build_hit_maps(hits: List[BlastHit]) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
        """
        Build forward and reverse hit mappings.
        
        Args:
            hits: List of BlastHit objects
            
        Returns:
            Tuple of (forward_map, reverse_map) where:
                - forward_map: query_id -> [subject_ids]
                - reverse_map: subject_id -> [query_ids]
        """
        forward_map = defaultdict(set)
        reverse_map = defaultdict(set)
        
        for hit in hits:
            forward_map[hit.query_id].add(hit.subject_id)
            reverse_map[hit.subject_id].add(hit.query_id)
        
        # Convert sets to lists
        return {k: list(v) for k, v in forward_map.items()}, {k: list(v) for k, v in reverse_map.items()}


class SyntenyAnalyzer:
    """Analyze synteny (gene order conservation) between assemblies."""
    
    @staticmethod
    def check_genes_adjacent(genes: List[Gene], max_gap: int = 10000) -> bool:
        """
        Check if a list of genes are adjacent in the genome.
        
        Args:
            genes: List of Gene objects
            max_gap: Maximum allowed gap between genes (bp)
            
        Returns:
            True if genes are on same chromosome and within max_gap
        """
        if len(genes) < 2:
            return True
        
        # Check all on same chromosome
        chromosomes = set(g.chromosome for g in genes)
        if len(chromosomes) > 1:
            return False
        
        # Sort genes by position
        sorted_genes = sorted(genes, key=lambda g: g.start)
        
        # Check gaps between consecutive genes
        for i in range(len(sorted_genes) - 1):
            gap = sorted_genes[i + 1].start - sorted_genes[i].end
            if gap > max_gap:
                return False
        
        return True
    
    @staticmethod
    def get_flanking_genes(target_gene: Gene, all_genes: Dict[str, Gene],
                          window: int = 5) -> Tuple[List[str], List[str]]:
        """
        Get genes flanking a target gene.
        
        Args:
            target_gene: The gene of interest
            all_genes: Dictionary of all genes
            window: Number of genes to retrieve on each side
            
        Returns:
            Tuple of (upstream_gene_ids, downstream_gene_ids)
        """
        # Get genes on same chromosome
        same_chrom = [
            g for g in all_genes.values()
            if g.chromosome == target_gene.chromosome
        ]
        
        # Sort by position
        sorted_genes = sorted(same_chrom, key=lambda g: g.start)
        
        # Find target position
        target_idx = None
        for i, gene in enumerate(sorted_genes):
            if gene.gene_id == target_gene.gene_id:
                target_idx = i
                break
        
        if target_idx is None:
            return [], []
        
        # Get flanking genes
        upstream = [
            sorted_genes[i].gene_id
            for i in range(max(0, target_idx - window), target_idx)
        ]
        
        downstream = [
            sorted_genes[i].gene_id
            for i in range(target_idx + 1, min(len(sorted_genes), target_idx + window + 1))
        ]
        
        return upstream, downstream
    
    @staticmethod
    def calculate_synteny_score(ref_flanking: Tuple[List[str], List[str]],
                               upd_flanking: Tuple[List[str], List[str]],
                               gene_name_map: Dict[str, str]) -> float:
        """
        Calculate synteny conservation score.
        
        Args:
            ref_flanking: (upstream, downstream) gene IDs in reference
            upd_flanking: (upstream, downstream) gene IDs in updated
            gene_name_map: Mapping from reference to updated gene IDs
            
        Returns:
            Synteny score (0-1, higher = more conserved)
        """
        ref_up, ref_down = ref_flanking
        upd_up, upd_down = upd_flanking
        
        # Map reference genes to updated genes
        ref_up_mapped = [gene_name_map.get(g, None) for g in ref_up]
        ref_down_mapped = [gene_name_map.get(g, None) for g in ref_down]
        
        # Count matches
        up_matches = len(set(ref_up_mapped) & set(upd_up))
        down_matches = len(set(ref_down_mapped) & set(upd_down))
        
        total_compared = len(ref_up) + len(ref_down)
        if total_compared == 0:
            return 0.0
        
        return (up_matches + down_matches) / total_compared


class GeneStructureAnalyzer:
    """Main analyzer for detecting gene splits and merges."""

    def __init__(self, ref_genes: Dict[str, Gene], upd_genes: Dict[str, Gene],
                 forward_blast: List[BlastHit], reverse_blast: List[BlastHit],
                 ref_transcript_map: Dict[str, str] = None,
                 upd_transcript_map: Dict[str, str] = None):
        """
        Initialize the analyzer.

        Args:
            ref_genes: Dictionary of reference genome genes
            upd_genes: Dictionary of updated genome genes
            forward_blast: BLAST hits (ref -> updated)
            reverse_blast: BLAST hits (updated -> ref)
            ref_transcript_map: Mapping from reference transcript IDs to gene IDs
            upd_transcript_map: Mapping from updated transcript IDs to gene IDs
        """
        self.ref_genes = ref_genes
        self.upd_genes = upd_genes
        self.forward_blast = forward_blast
        self.reverse_blast = reverse_blast
        self.ref_transcript_map = ref_transcript_map or {}
        self.upd_transcript_map = upd_transcript_map or {}

        # Build hit maps with gene IDs (converting from transcript IDs if needed)
        self.forward_map, _ = self._build_gene_hit_maps(
            forward_blast, self.ref_transcript_map, self.upd_transcript_map
        )
        self.reverse_map, _ = self._build_gene_hit_maps(
            reverse_blast, self.upd_transcript_map, self.ref_transcript_map
        )

        # Build comprehensive DataFrames for advanced analysis
        self.forward_df = self._hits_to_dataframe(forward_blast)
        self.reverse_df = self._hits_to_dataframe(reverse_blast)

        logger.info("GeneStructureAnalyzer initialized")

    @staticmethod
    def _build_gene_hit_maps(hits: List[BlastHit],
                            query_transcript_map: Dict[str, str],
                            subject_transcript_map: Dict[str, str]) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
        """
        Build hit maps using gene IDs instead of transcript IDs.

        Args:
            hits: List of BlastHit objects (with transcript IDs)
            query_transcript_map: Mapping from query transcript IDs to gene IDs
            subject_transcript_map: Mapping from subject transcript IDs to gene IDs

        Returns:
            Tuple of (forward_map, reverse_map) using gene IDs
        """
        forward_map = defaultdict(set)
        reverse_map = defaultdict(set)

        for hit in hits:
            # Convert transcript IDs to gene IDs
            query_gene_id = query_transcript_map.get(hit.query_id, hit.query_id)
            subject_gene_id = subject_transcript_map.get(hit.subject_id, hit.subject_id)

            forward_map[query_gene_id].add(subject_gene_id)
            reverse_map[subject_gene_id].add(query_gene_id)

        # Convert sets to lists
        return {k: list(v) for k, v in forward_map.items()}, {k: list(v) for k, v in reverse_map.items()}

    @staticmethod
    def _hits_to_dataframe(hits: List[BlastHit]) -> pd.DataFrame:
        """
        Convert BlastHit objects to pandas DataFrame.

        Args:
            hits: List of BlastHit objects

        Returns:
            DataFrame with all hit information
        """
        records = []
        for hit in hits:
            records.append({
                'qseqid': hit.query_id,
                'sseqid': hit.subject_id,
                'pident': hit.pident,
                'length': hit.length,
                'qstart': hit.qstart,
                'qend': hit.qend,
                'qlen': hit.qlen,
                'sstart': hit.sstart,
                'send': hit.send,
                'slen': hit.slen,
                'evalue': hit.evalue,
                'bitscore': hit.bitscore,
                'qcoverage': hit.query_coverage,
                'scoverage': hit.subject_coverage
            })
        return pd.DataFrame(records) if records else pd.DataFrame()

    def get_bidirectional_best_hits(self, min_identity: float = 30.0,
                                   min_coverage: float = 50.0) -> pd.DataFrame:
        """
        Perform bidirectional best hit (BBH) analysis to identify orthologs.

        This method finds reciprocal best hits between reference and updated genomes,
        which are strong candidates for one-to-one orthologous relationships.

        Args:
            min_identity: Minimum percent identity threshold
            min_coverage: Minimum query coverage threshold

        Returns:
            DataFrame with BBH results containing:
                - ref_gene: Reference gene ID
                - upd_gene: Updated gene ID
                - pident_fwd: Percent identity (forward)
                - pident_rev: Percent identity (reverse)
                - evalue_fwd: E-value (forward)
                - evalue_rev: E-value (reverse)
                - bitscore_fwd: Bitscore (forward)
                - bitscore_rev: Bitscore (reverse)
                - avg_pident: Average percent identity
                - avg_coverage: Average coverage
        """
        logger.info("Performing bidirectional best hit analysis...")

        if self.forward_df.empty or self.reverse_df.empty:
            logger.warning("No BLAST hits available for BBH analysis")
            return pd.DataFrame()

        # Filter by quality thresholds
        fwd_filtered = self.forward_df[
            (self.forward_df['pident'] >= min_identity) &
            (self.forward_df['qcoverage'] >= min_coverage)
        ].copy()

        rev_filtered = self.reverse_df[
            (self.reverse_df['pident'] >= min_identity) &
            (self.reverse_df['qcoverage'] >= min_coverage)
        ].copy()

        if fwd_filtered.empty or rev_filtered.empty:
            logger.warning("No hits pass quality filters for BBH analysis")
            return pd.DataFrame()

        # Get best hits in forward direction (ref -> upd)
        best_fwd = fwd_filtered.loc[
            fwd_filtered.groupby('qseqid')['evalue'].idxmin()
        ][['qseqid', 'sseqid', 'pident', 'evalue', 'bitscore', 'qcoverage', 'scoverage']].copy()
        best_fwd.columns = ['ref_gene', 'upd_gene', 'pident_fwd', 'evalue_fwd',
                           'bitscore_fwd', 'qcov_fwd', 'scov_fwd']

        # Get best hits in reverse direction (upd -> ref)
        best_rev = rev_filtered.loc[
            rev_filtered.groupby('qseqid')['evalue'].idxmin()
        ][['qseqid', 'sseqid', 'pident', 'evalue', 'bitscore', 'qcoverage', 'scoverage']].copy()
        best_rev.columns = ['upd_gene', 'ref_gene', 'pident_rev', 'evalue_rev',
                           'bitscore_rev', 'qcov_rev', 'scov_rev']

        # Merge to find reciprocal best hits
        bbh = pd.merge(
            best_fwd,
            best_rev,
            on=['ref_gene', 'upd_gene'],
            how='inner'
        )

        # Calculate average statistics
        bbh['avg_pident'] = (bbh['pident_fwd'] + bbh['pident_rev']) / 2
        bbh['avg_coverage'] = (bbh['qcov_fwd'] + bbh['qcov_rev'] +
                               bbh['scov_fwd'] + bbh['scov_rev']) / 4

        # Sort by average identity (descending)
        bbh = bbh.sort_values('avg_pident', ascending=False)

        logger.info(f"Found {len(bbh)} bidirectional best hits (orthologs)")

        return bbh

    def identify_one_to_one_orthologs(self, min_identity: float = 70.0,
                                      min_coverage: float = 70.0) -> Dict[str, str]:
        """
        Identify high-confidence one-to-one orthologous gene pairs.

        Args:
            min_identity: Minimum average percent identity
            min_coverage: Minimum average coverage

        Returns:
            Dictionary mapping reference gene IDs to updated gene IDs
        """
        bbh = self.get_bidirectional_best_hits(min_identity, min_coverage)

        if bbh.empty:
            return {}

        # Filter by quality
        high_conf = bbh[
            (bbh['avg_pident'] >= min_identity) &
            (bbh['avg_coverage'] >= min_coverage)
        ]

        orthologs = dict(zip(high_conf['ref_gene'], high_conf['upd_gene']))

        logger.info(f"Identified {len(orthologs)} high-confidence orthologs")

        return orthologs
    
    def detect_splits(self, min_confidence: float = 0.7, require_adjacency: bool = True) -> List[GeneRelationship]:
        """
        Detect gene splits (1 reference gene -> multiple updated genes).

        Args:
            min_confidence: Minimum confidence score to report
            require_adjacency: If True, only report splits where genes are adjacent (default: True)

        Returns:
            List of GeneRelationship objects representing splits
        """
        splits = []

        adjacency_mode = "with adjacency requirement" if require_adjacency else "without adjacency requirement"
        logger.info(f"Detecting gene splits {adjacency_mode}...")

        for ref_id, upd_ids in self.forward_map.items():
            # Looking for 1 -> many relationships
            if len(upd_ids) < 2:
                continue

            # Remove duplicates
            upd_ids = list(set(upd_ids))

            # Verify reciprocal relationship
            reciprocal = all(
                ref_id in self.reverse_map.get(upd_id, [])
                for upd_id in upd_ids
            )

            if not reciprocal:
                continue

            # Get gene objects
            ref_gene = self.ref_genes[ref_id]
            upd_genes_list = [self.upd_genes[uid] for uid in upd_ids if uid in self.upd_genes]

            if len(upd_genes_list) < 2:
                continue

            # Check if updated genes are adjacent
            adjacent = SyntenyAnalyzer.check_genes_adjacent(upd_genes_list)

            # Skip if adjacency is required but genes are not adjacent
            if require_adjacency and not adjacent:
                continue
            
            # Calculate coverage
            coverage_score = self._calculate_split_coverage(ref_gene, upd_genes_list)
            
            # Calculate confidence
            confidence = self._calculate_confidence(
                reciprocal=True,
                adjacent=adjacent,
                coverage=coverage_score
            )
            
            if confidence >= min_confidence:
                relationship = GeneRelationship(
                    relationship_type='split',
                    ref_genes=[ref_id],
                    updated_genes=upd_ids,
                    confidence_score=confidence,
                    evidence={
                        'reciprocal': reciprocal,
                        'adjacent': adjacent,
                        'coverage': coverage_score,
                        'ref_length': ref_gene.length,
                        'updated_lengths': [g.length for g in upd_genes_list]
                    }
                )
                splits.append(relationship)
        
        logger.info(f"Detected {len(splits)} gene splits")
        return splits
    
    def detect_merges(self, min_confidence: float = 0.7, require_adjacency: bool = True) -> List[GeneRelationship]:
        """
        Detect gene merges (multiple reference genes -> 1 updated gene).

        Args:
            min_confidence: Minimum confidence score to report
            require_adjacency: If True, only report merges where genes are adjacent (default: True)

        Returns:
            List of GeneRelationship objects representing merges
        """
        merges = []

        adjacency_mode = "with adjacency requirement" if require_adjacency else "without adjacency requirement"
        logger.info(f"Detecting gene merges {adjacency_mode}...")

        for upd_id, ref_ids in self.reverse_map.items():
            # Looking for many -> 1 relationships
            if len(ref_ids) < 2:
                continue

            # Remove duplicates
            ref_ids = list(set(ref_ids))

            # Verify reciprocal relationship
            reciprocal = all(
                upd_id in self.forward_map.get(ref_id, [])
                for ref_id in ref_ids
            )

            if not reciprocal:
                continue

            # Get gene objects
            upd_gene = self.upd_genes[upd_id]
            ref_genes_list = [self.ref_genes[rid] for rid in ref_ids if rid in self.ref_genes]

            if len(ref_genes_list) < 2:
                continue

            # Check if reference genes were adjacent
            adjacent = SyntenyAnalyzer.check_genes_adjacent(ref_genes_list)

            # Skip if adjacency is required but genes are not adjacent
            if require_adjacency and not adjacent:
                continue
            
            # Calculate coverage
            coverage_score = self._calculate_merge_coverage(ref_genes_list, upd_gene)
            
            # Calculate confidence
            confidence = self._calculate_confidence(
                reciprocal=True,
                adjacent=adjacent,
                coverage=coverage_score
            )
            
            if confidence >= min_confidence:
                relationship = GeneRelationship(
                    relationship_type='merge',
                    ref_genes=ref_ids,
                    updated_genes=[upd_id],
                    confidence_score=confidence,
                    evidence={
                        'reciprocal': reciprocal,
                        'adjacent': adjacent,
                        'coverage': coverage_score,
                        'ref_lengths': [g.length for g in ref_genes_list],
                        'updated_length': upd_gene.length
                    }
                )
                merges.append(relationship)
        
        logger.info(f"Detected {len(merges)} gene merges")
        return merges
    
    def _calculate_split_coverage(self, ref_gene: Gene, upd_genes: List[Gene]) -> float:
        """
        Calculate how well the updated genes cover the reference gene.
        
        Returns:
            Coverage score (0-1)
        """
        # Simple length-based coverage
        total_upd_length = sum(g.length for g in upd_genes)
        return min(total_upd_length / ref_gene.length, 1.0)
    
    def _calculate_merge_coverage(self, ref_genes: List[Gene], upd_gene: Gene) -> float:
        """
        Calculate how well the updated gene covers the reference genes.
        
        Returns:
            Coverage score (0-1)
        """
        # Simple length-based coverage
        total_ref_length = sum(g.length for g in ref_genes)
        return min(upd_gene.length / total_ref_length, 1.0)
    
    def _calculate_confidence(self, reciprocal: bool, adjacent: bool,
                            coverage: float) -> float:
        """
        Calculate overall confidence score for a relationship.
        
        Args:
            reciprocal: Reciprocal best hit confirmed
            adjacent: Genes are adjacent
            coverage: Coverage score
            
        Returns:
            Confidence score (0-1)
        """
        # Weighted scoring
        score = 0.0
        
        if reciprocal:
            score += 0.4  # Reciprocal is most important
        
        if adjacent:
            score += 0.3  # Adjacency is important
        
        score += coverage * 0.3  # Coverage contributes proportionally
        
        return score


class ResultsExporter:
    """Export analysis results to various formats."""
    
    @staticmethod
    def to_dataframe(relationships: List[GeneRelationship]) -> pd.DataFrame:
        """
        Convert relationships to a pandas DataFrame.
        
        Args:
            relationships: List of GeneRelationship objects
            
        Returns:
            DataFrame with relationship information
        """
        records = []
        
        for rel in relationships:
            record = {
                'type': rel.relationship_type,
                'ref_genes': ','.join(rel.ref_genes),
                'updated_genes': ','.join(rel.updated_genes),
                'confidence': rel.confidence_score,
                'reciprocal': rel.evidence.get('reciprocal', False),
                'adjacent': rel.evidence.get('adjacent', False),
                'coverage': rel.evidence.get('coverage', 0.0)
            }
            records.append(record)
        
        return pd.DataFrame(records)
    
    @staticmethod
    def save_results(relationships: List[GeneRelationship], output_file: str) -> None:
        """
        Save results to a TSV file.
        
        Args:
            relationships: List of GeneRelationship objects
            output_file: Path to output file
        """
        df = ResultsExporter.to_dataframe(relationships)
        df.to_csv(output_file, sep='\t', index=False)
        logger.info(f"Results saved to: {output_file}")
    
    @staticmethod
    def print_summary(splits: List[GeneRelationship], merges: List[GeneRelationship]) -> None:
        """
        Print a summary of detected changes.
        
        Args:
            splits: List of gene splits
            merges: List of gene merges
        """
        print("\n" + "="*60)
        print("GENE STRUCTURE CHANGE ANALYSIS SUMMARY")
        print("="*60)
        print(f"\nTotal gene splits detected: {len(splits)}")
        print(f"Total gene merges detected: {len(merges)}")
        
        if splits:
            print("\n--- High Confidence Splits (top 5) ---")
            top_splits = sorted(splits, key=lambda x: x.confidence_score, reverse=True)[:5]
            for i, split in enumerate(top_splits, 1):
                print(f"\n{i}. Reference gene: {split.ref_genes[0]}")
                print(f"   Split into: {', '.join(split.updated_genes)}")
                print(f"   Confidence: {split.confidence_score:.2f}")
                print(f"   Coverage: {split.evidence['coverage']:.2%}")
        
        if merges:
            print("\n--- High Confidence Merges (top 5) ---")
            top_merges = sorted(merges, key=lambda x: x.confidence_score, reverse=True)[:5]
            for i, merge in enumerate(top_merges, 1):
                print(f"\n{i}. Reference genes: {', '.join(merge.ref_genes)}")
                print(f"   Merged into: {merge.updated_genes[0]}")
                print(f"   Confidence: {merge.confidence_score:.2f}")
                print(f"   Coverage: {merge.evidence['coverage']:.2%}")
        
        print("\n" + "="*60 + "\n")


def main():
    """Main workflow execution."""
    
    # Example usage - you'll need to provide your actual file paths
    print("Gene Structure Change Analyzer")
    print("="*60)
    print("\nThis script requires:")
    print("1. Reference genome GFF file")
    print("2. Updated genome GFF file")
    print("3. Reference protein FASTA")
    print("4. Updated protein FASTA")
    print("5. BLAST results (ref -> updated)")
    print("6. BLAST results (updated -> ref)")
    print("\nSee example_workflow.py for a complete working example")
    print("="*60)


if __name__ == '__main__':
    main()
