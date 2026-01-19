"""
Pairwise protein sequence alignment using Biopython.

Performs local alignment between two protein sequences and calculates
alignment statistics including score, identity, and coverage.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Generator, List, Optional, Tuple, Union

from Bio import Align, SeqIO
from Bio.Seq import Seq


@dataclass
class AlignmentResult:
    """Container for alignment results with named access."""
    score: float
    identity_percent: float
    coverage_query: float
    coverage_ref: float
    aligned_length: int
    identical_count: int
    mismatch_count: int
    gap_count: int
    alignment: object  # Biopython Alignment object


def local_alignment_similarity(
    seq1: str | Seq,
    seq2: str | Seq,
    match_score: float = 1.0,
    mismatch_score: float = 0.0,
    open_gap_score: float = -1.0,
    extend_gap_score: float = -0.5,
) -> AlignmentResult:
    """
    Perform local alignment and calculate similarity metrics.

    Args:
        seq1: Reference sequence (string or Biopython Seq)
        seq2: Query sequence (string or Biopython Seq)
        match_score: Score for matching residues
        mismatch_score: Penalty for mismatches
        open_gap_score: Penalty for opening a gap
        extend_gap_score: Penalty for extending a gap

    Returns:
        AlignmentResult with score, identity, coverage, and alignment object
    """
    aligner = Align.PairwiseAligner()
    aligner.mode = 'local'
    aligner.match_score = match_score
    aligner.mismatch_score = mismatch_score
    aligner.open_gap_score = open_gap_score
    aligner.extend_gap_score = extend_gap_score

    alignments = aligner.align(seq1, seq2)

    if not alignments:
        return AlignmentResult(
            score=0.0,
            identity_percent=0.0,
            coverage_query=0.0,
            coverage_ref=0.0,
            aligned_length=0,
            identical_count=0,
            mismatch_count=0,
            gap_count=0,
            alignment=None,
        )

    best = alignments[0]
    score = best.score

    # Calculate BLAST-style alignment statistics
    stats = calculate_alignment_stats(best)

    # Calculate aligned length from coordinate blocks (ungapped)
    aligned_length = sum(end - start for start, end in best.aligned[0])

    # Coverage: how much of each sequence is in the alignment
    coverage_ref = (aligned_length / len(seq1) * 100) if len(seq1) > 0 else 0.0
    coverage_query = (aligned_length / len(seq2) * 100) if len(seq2) > 0 else 0.0

    return AlignmentResult(
        score=score,
        identity_percent=stats.identity_percent,
        coverage_query=coverage_query,
        coverage_ref=coverage_ref,
        aligned_length=stats.alignment_length,
        identical_count=stats.identical,
        mismatch_count=stats.mismatches,
        gap_count=stats.gaps,
        alignment=best,
    )


@dataclass
class AlignmentStats:
    """BLAST-style alignment statistics."""
    identical: int
    mismatches: int
    gaps: int
    alignment_length: int
    identity_percent: float


def calculate_alignment_stats(alignment) -> AlignmentStats:
    """
    Calculate BLAST-style alignment statistics.

    BLAST-style identity = (identical matches) / (alignment length) * 100

    The alignment length includes all positions: matches, mismatches, and gaps.
    This is the standard metric used in BLAST output and most sequence
    comparison tools.

    Args:
        alignment: Biopython alignment object

    Returns:
        AlignmentStats with counts and identity percentage
    """
    if alignment is None:
        return AlignmentStats(0, 0, 0, 0, 0.0)

    # Extract aligned sequences (includes gap characters '-')
    # alignment[0] = reference with gaps, alignment[1] = query with gaps
    seq1_aligned = str(alignment[0])
    seq2_aligned = str(alignment[1])

    alignment_length = len(seq1_aligned)
    if alignment_length == 0:
        return AlignmentStats(0, 0, 0, 0, 0.0)

    identical = 0
    mismatches = 0
    gaps = 0

    for res1, res2 in zip(seq1_aligned, seq2_aligned):
        if res1 == '-' or res2 == '-':
            gaps += 1
        elif res1 == res2:
            identical += 1
        else:
            mismatches += 1

    identity_percent = (identical / alignment_length) * 100

    return AlignmentStats(
        identical=identical,
        mismatches=mismatches,
        gaps=gaps,
        alignment_length=alignment_length,
        identity_percent=identity_percent,
    )


def read_first_sequence(fasta_path: str | Path) -> Optional[Seq]:
    """
    Read the first sequence from a FASTA file.

    Args:
        fasta_path: Path to FASTA file

    Returns:
        Biopython Seq object, or None if file is empty/invalid
    """
    path = Path(fasta_path)
    if not path.exists():
        raise FileNotFoundError(f"FASTA file not found: {path}")

    for record in SeqIO.parse(path, "fasta"):
        return record.seq

    return None


def read_all_sequences(fasta_path: str | Path) -> Dict[str, Seq]:
    """
    Read ALL sequences from a FASTA file.

    Args:
        fasta_path: Path to FASTA file

    Returns:
        Dictionary mapping sequence ID to Seq object
    """
    path = Path(fasta_path)
    if not path.exists():
        raise FileNotFoundError(f"FASTA file not found: {path}")

    sequences = {}
    for record in SeqIO.parse(path, "fasta"):
        sequences[record.id] = record.seq

    return sequences


@dataclass
class PairwiseResult:
    """Container for a single pairwise alignment result with IDs."""
    ref_id: str
    query_id: str
    ref_len: int
    query_len: int
    score: float
    identity_percent: float
    coverage_query: float
    coverage_ref: float
    aligned_length: int
    identical_count: int
    mismatch_count: int
    gap_count: int


def align_all_vs_all(
    ref_fasta: str | Path,
    query_fasta: str | Path,
    min_identity: float = 0.0,
    min_coverage: float = 0.0,
    **aligner_kwargs,
) -> Generator[PairwiseResult, None, None]:
    """
    Perform all-vs-all alignment between two FASTA files.

    Yields results as a generator to handle large files efficiently.

    Args:
        ref_fasta: Path to reference FASTA file
        query_fasta: Path to query FASTA file
        min_identity: Minimum identity % to report (default: 0, report all)
        min_coverage: Minimum coverage % to report (default: 0, report all)
        **aligner_kwargs: Additional arguments for local_alignment_similarity

    Yields:
        PairwiseResult for each ref-query pair that passes filters
    """
    ref_seqs = read_all_sequences(ref_fasta)
    query_seqs = read_all_sequences(query_fasta)

    total_pairs = len(ref_seqs) * len(query_seqs)
    print(f"Aligning {len(ref_seqs)} ref × {len(query_seqs)} query = {total_pairs} pairs",
          file=sys.stderr)

    completed = 0
    for ref_id, ref_seq in ref_seqs.items():
        for query_id, query_seq in query_seqs.items():
            result = local_alignment_similarity(ref_seq, query_seq, **aligner_kwargs)

            # Apply filters
            if result.identity_percent < min_identity:
                continue
            if result.coverage_ref < min_coverage and result.coverage_query < min_coverage:
                continue

            completed += 1
            if completed % 1000 == 0:
                print(f"  Completed {completed}/{total_pairs} pairs...", file=sys.stderr)

            yield PairwiseResult(
                ref_id=ref_id,
                query_id=query_id,
                ref_len=len(ref_seq),
                query_len=len(query_seq),
                score=result.score,
                identity_percent=result.identity_percent,
                coverage_query=result.coverage_query,
                coverage_ref=result.coverage_ref,
                aligned_length=result.aligned_length,
                identical_count=result.identical_count,
                mismatch_count=result.mismatch_count,
                gap_count=result.gap_count,
            )


def align_all_vs_all_to_tsv(
    ref_fasta: str | Path,
    query_fasta: str | Path,
    output_path: str | Path,
    min_identity: float = 0.0,
    min_coverage: float = 0.0,
    **aligner_kwargs,
) -> int:
    """
    Perform all-vs-all alignment and write results to TSV file.

    Args:
        ref_fasta: Path to reference FASTA file
        query_fasta: Path to query FASTA file
        output_path: Output TSV file path
        min_identity: Minimum identity % to report
        min_coverage: Minimum coverage % to report
        **aligner_kwargs: Additional arguments for local_alignment_similarity

    Returns:
        Number of alignments written
    """
    header = [
        "ref_id", "query_id", "ref_len", "query_len",
        "score", "identity_percent", "coverage_ref", "coverage_query",
        "aligned_length", "identical_count", "mismatch_count", "gap_count"
    ]

    count = 0
    with open(output_path, 'w') as f:
        f.write("\t".join(header) + "\n")

        for result in align_all_vs_all(
            ref_fasta, query_fasta, min_identity, min_coverage, **aligner_kwargs
        ):
            row = [
                result.ref_id,
                result.query_id,
                str(result.ref_len),
                str(result.query_len),
                f"{result.score:.1f}",
                f"{result.identity_percent:.2f}",
                f"{result.coverage_ref:.2f}",
                f"{result.coverage_query:.2f}",
                str(result.aligned_length),
                str(result.identical_count),
                str(result.mismatch_count),
                str(result.gap_count),
            ]
            f.write("\t".join(row) + "\n")
            count += 1

    print(f"Wrote {count} alignments to {output_path}", file=sys.stderr)
    return count


def align_fasta_files(
    ref_fasta: str | Path,
    query_fasta: str | Path,
    **aligner_kwargs,
) -> AlignmentResult:
    """
    Align sequences from two FASTA files.

    Args:
        ref_fasta: Path to reference FASTA file
        query_fasta: Path to query FASTA file
        **aligner_kwargs: Additional arguments for local_alignment_similarity

    Returns:
        AlignmentResult
    """
    ref_seq = read_first_sequence(ref_fasta)
    query_seq = read_first_sequence(query_fasta)

    if ref_seq is None:
        raise ValueError(f"No sequences found in reference file: {ref_fasta}")
    if query_seq is None:
        raise ValueError(f"No sequences found in query file: {query_fasta}")

    return local_alignment_similarity(ref_seq, query_seq, **aligner_kwargs)


def main():
    """Command-line interface for pairwise protein alignment."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Pairwise protein sequence alignment using Biopython",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single alignment (first sequence from each file)
  python pariwise_align_prot.py ref.faa query.faa

  # All-vs-all alignment to TSV
  python pariwise_align_prot.py ref.faa query.faa --all-vs-all -o results.tsv

  # All-vs-all with filters
  python pariwise_align_prot.py ref.faa query.faa --all-vs-all -o results.tsv \\
      --min-identity 30 --min-coverage 50
        """
    )

    parser.add_argument("ref_fasta", help="Reference FASTA file")
    parser.add_argument("query_fasta", help="Query FASTA file")
    parser.add_argument(
        "--all-vs-all", "-a",
        action="store_true",
        help="Align ALL sequences (N×M comparisons)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output TSV file (required for --all-vs-all)"
    )
    parser.add_argument(
        "--min-identity",
        type=float,
        default=0.0,
        help="Minimum identity %% to report (default: 0)"
    )
    parser.add_argument(
        "--min-coverage",
        type=float,
        default=0.0,
        help="Minimum coverage %% to report (default: 0)"
    )

    args = parser.parse_args()

    # Validate arguments
    if args.all_vs_all and not args.output:
        parser.error("--all-vs-all requires --output/-o")

    try:
        if args.all_vs_all:
            # All-vs-all mode
            print(f"Reference: {args.ref_fasta}")
            print(f"Query: {args.query_fasta}")
            print(f"Output: {args.output}")
            print(f"Filters: identity >= {args.min_identity}%, coverage >= {args.min_coverage}%")
            print("-" * 50)

            count = align_all_vs_all_to_tsv(
                args.ref_fasta,
                args.query_fasta,
                args.output,
                min_identity=args.min_identity,
                min_coverage=args.min_coverage,
            )
            print(f"\nDone! {count} alignments written to {args.output}")

        else:
            # Single alignment mode (original behavior)
            print(f"Reference: {args.ref_fasta}")
            print(f"Query: {args.query_fasta}")
            print("-" * 50)

            result = align_fasta_files(args.ref_fasta, args.query_fasta)
            print(f"Score: {result.score}")
            print(f"Identity: {result.identity_percent:.1f}% "
                  f"({result.identical_count}/{result.aligned_length})")
            print(f"Mismatches: {result.mismatch_count}")
            print(f"Gaps: {result.gap_count}")
            print(f"Coverage (ref): {result.coverage_ref:.1f}%")
            print(f"Coverage (query): {result.coverage_query:.1f}%")
            print(f"Alignment length: {result.aligned_length}")
            print("-" * 50)
            if result.alignment:
                print("Alignment:")
                print(result.alignment)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()