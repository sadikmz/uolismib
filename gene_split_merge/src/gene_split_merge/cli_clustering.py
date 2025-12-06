#!/usr/bin/env python3
"""
DIAMOND Clustering Workflow
============================
Command-line tool for running DIAMOND clustering workflows with flexible options.

Supports:
- Multiple clustering algorithms (linclust, cluster, deepclust, recluster, realign)
- Database selection (ref, qry, all)
- Flexible parameter specification
- Automatic sequence ID renaming for combined databases

Author: Bioinformatics Workflow
Date: 2025-12-06
"""

import argparse
import sys
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord
import tempfile
import subprocess

from .clustering import DiamondClusterer
from .analyzer import GFFParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ClusteringWorkflow:
    """
    Manage DIAMOND clustering workflows with database preparation and parameter handling.
    """

    VALID_WORKFLOWS = ['linclust', 'cluster', 'deepclust', 'recluster', 'realign']
    VALID_DATABASES = ['ref', 'qry', 'all']

    def __init__(self, args):
        """
        Initialize clustering workflow.

        Args:
            args: Parsed command-line arguments
        """
        self.args = args
        self.clusterer = DiamondClusterer()
        self.temp_files = []

    def __del__(self):
        """Cleanup temporary files."""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.debug(f"Cleaned up temporary file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to clean up {temp_file}: {e}")

    def parse_parameters(self, param_string: Optional[str]) -> Dict[str, str]:
        """
        Parse space-separated parameters into dictionary.

        Format: --memory-limit 10G --approx-id 80 --member-cover 70

        Args:
            param_string: Space-separated parameter string

        Returns:
            Dictionary of parameter key-value pairs
        """
        if not param_string:
            return {}

        params = {}
        tokens = param_string.split()
        i = 0

        while i < len(tokens):
            token = tokens[i]

            # Check if this is a parameter (starts with --)
            if token.startswith('--'):
                key = token.lstrip('-').replace('-', '_')

                # Check if next token is a value (doesn't start with --)
                if i + 1 < len(tokens) and not tokens[i + 1].startswith('--'):
                    value = tokens[i + 1]
                    params[key] = value
                    i += 2  # Skip both parameter and value
                else:
                    # Boolean flag (no value)
                    params[key] = True
                    i += 1
            else:
                logger.warning(f"Skipping unexpected token: {token}")
                i += 1

        logger.info(f"Parsed parameters: {params}")
        return params

    def prepare_database(self, database_option: str) -> str:
        """
        Prepare the appropriate database file based on user selection.

        Args:
            database_option: 'ref', 'qry', or 'all'

        Returns:
            Path to the prepared database file
        """
        logger.info(f"Preparing database: {database_option}")

        if database_option == 'ref':
            if not self.args.ref_proteins:
                raise ValueError("--ref-proteins required when using --database ref")
            return self.args.ref_proteins

        elif database_option == 'qry':
            if not self.args.qry_proteins:
                raise ValueError("--qry-proteins required when using --database qry")
            return self.args.qry_proteins

        elif database_option == 'all':
            if not self.args.ref_proteins or not self.args.qry_proteins:
                raise ValueError("Both --ref-proteins and --qry-proteins required when using --database all")
            return self._combine_databases()

        else:
            raise ValueError(f"Invalid database option: {database_option}")

    def _combine_databases(self) -> str:
        """
        Combine reference and query protein databases with renamed IDs.

        Adds '_REF' suffix to reference sequences and '_QRY' suffix to query sequences
        to avoid ID conflicts.

        Returns:
            Path to combined FASTA file
        """
        logger.info("Combining reference and query databases...")

        # Create temporary combined file
        temp_fd, temp_path = tempfile.mkstemp(suffix='_combined.fasta', prefix='cluster_')
        os.close(temp_fd)
        self.temp_files.append(temp_path)

        combined_records = []
        ref_count = 0
        qry_count = 0

        # Read reference proteins and add _REF suffix
        logger.info(f"Reading reference proteins from: {self.args.ref_proteins}")
        for record in SeqIO.parse(self.args.ref_proteins, 'fasta'):
            new_id = f"{record.id}_REF"
            new_record = SeqRecord(
                record.seq,
                id=new_id,
                description=f"{record.description} [REF]"
            )
            combined_records.append(new_record)
            ref_count += 1

        # Read query proteins and add _QRY suffix
        logger.info(f"Reading query proteins from: {self.args.qry_proteins}")
        for record in SeqIO.parse(self.args.qry_proteins, 'fasta'):
            new_id = f"{record.id}_QRY"
            new_record = SeqRecord(
                record.seq,
                id=new_id,
                description=f"{record.description} [QRY]"
            )
            combined_records.append(new_record)
            qry_count += 1

        # Write combined file
        SeqIO.write(combined_records, temp_path, 'fasta')

        logger.info(f"Combined database created: {temp_path}")
        logger.info(f"  Reference sequences: {ref_count} (suffix: _REF)")
        logger.info(f"  Query sequences: {qry_count} (suffix: _QRY)")
        logger.info(f"  Total sequences: {ref_count + qry_count}")

        return temp_path

    def run_workflow(self):
        """
        Execute the selected DIAMOND clustering workflow.
        """
        workflow = self.args.workflow
        logger.info(f"Running DIAMOND clustering workflow: {workflow}")

        # Prepare database
        db_file = self.prepare_database(self.args.database)

        # Parse additional parameters
        extra_params = self.parse_parameters(self.args.params)

        # Get output file
        output_file = self.args.output

        # Ensure output directory exists
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")

        # Run the appropriate workflow
        if workflow == 'linclust':
            df = self.clusterer.linclust(
                input_file=db_file,
                output_file=output_file,
                threads=self.args.threads,
                **extra_params
            )

        elif workflow == 'cluster':
            df = self.clusterer.cluster(
                input_file=db_file,
                output_file=output_file,
                threads=self.args.threads,
                **extra_params
            )

        elif workflow == 'deepclust':
            df = self.clusterer.deepclust(
                input_file=db_file,
                output_file=output_file,
                threads=self.args.threads,
                **extra_params
            )

        elif workflow == 'recluster':
            if not self.args.clusters:
                raise ValueError("--clusters required for recluster workflow")
            df = self.clusterer.recluster(
                input_file=db_file,
                clusters_file=self.args.clusters,
                output_file=output_file,
                threads=self.args.threads,
                **extra_params
            )

        elif workflow == 'realign':
            if not self.args.clusters:
                raise ValueError("--clusters required for realign workflow")
            df = self._run_realign(db_file, output_file, extra_params)

        else:
            raise ValueError(f"Unknown workflow: {workflow}")

        # Print summary
        self._print_summary(df, workflow)

        return df

    def _run_realign(self, db_file: str, output_file: str, params: Dict) -> None:
        """
        Run DIAMOND realign workflow.

        Args:
            db_file: Database file
            output_file: Output file
            params: Additional parameters
        """
        logger.info("Running DIAMOND realign workflow...")

        cmd = [
            'diamond', 'realign',
            '-d', db_file,
            '--clusters', self.args.clusters,
            '-o', output_file,
            '--threads', str(self.args.threads)
        ]

        # Add extra parameters
        for key, value in params.items():
            cmd.append(f'--{key.replace("_", "-")}')
            if value is not True:
                cmd.append(str(value))

        logger.info(f"Running command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("Realign completed successfully")
            if result.stdout:
                logger.debug(f"Output: {result.stdout}")

        except subprocess.CalledProcessError as e:
            error_msg = f"Realign failed: {e.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

        # Return None for realign (output format may vary)
        return None

    def _print_summary(self, df, workflow: str):
        """
        Print clustering summary.

        Args:
            df: Clustering DataFrame (or None for realign)
            workflow: Workflow name
        """
        print("\n" + "="*60)
        print(f"DIAMOND CLUSTERING SUMMARY - {workflow.upper()}")
        print("="*60)

        print(f"\nWorkflow: {workflow}")
        print(f"Database: {self.args.database}")
        print(f"Output: {self.args.output}")

        if df is not None:
            print(f"\nResults:")
            print(f"  Total sequences: {len(df)}")
            print(f"  Total clusters: {df['cluster_number'].nunique()}")

            # Cluster size distribution
            cluster_sizes = df.groupby('cluster_number').size()
            print(f"\nCluster size distribution:")
            print(f"  Singletons: {(cluster_sizes == 1).sum()}")
            print(f"  2-5 members: {((cluster_sizes >= 2) & (cluster_sizes <= 5)).sum()}")
            print(f"  6-10 members: {((cluster_sizes >= 6) & (cluster_sizes <= 10)).sum()}")
            print(f"  >10 members: {(cluster_sizes > 10).sum()}")

            if (cluster_sizes > 1).any():
                print(f"\nLargest clusters:")
                largest = df.groupby(['cluster_number', 'representative']).size().sort_values(ascending=False).head(5)
                for (cluster_num, rep), size in largest.items():
                    print(f"  Cluster {cluster_num}: {size} members (rep: {rep})")

        else:
            print(f"\nRealign workflow completed. Check output file for results.")

        print("\n" + "="*60 + "\n")


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='DIAMOND Clustering Workflow',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:

  1. Fast clustering of reference proteins at 90%% identity:
     python run_clustering.py \\
         --workflow linclust \\
         --database ref \\
         --ref-proteins reference_proteins.fasta \\
         --output results/ref_clusters.tsv \\
         --params "--memory-limit 64G --approx-id 90 --member-cover 80"

  2. Sensitive clustering of query proteins at 50%% identity:
     python run_clustering.py \\
         --workflow cluster \\
         --database qry \\
         --qry-proteins query_proteins.fasta \\
         --output results/qry_clusters.tsv \\
         --params "--memory-limit 64G --approx-id 50"

  3. Combined database clustering (ref + qry with renamed IDs):
     python run_clustering.py \\
         --workflow linclust \\
         --database all \\
         --ref-proteins reference_proteins.fasta \\
         --qry-proteins query_proteins.fasta \\
         --output results/combined_clusters.tsv \\
         --params "--memory-limit 64G --approx-id 80"

  4. Deep clustering (no identity cutoff):
     python run_clustering.py \\
         --workflow deepclust \\
         --database all \\
         --ref-proteins reference_proteins.fasta \\
         --qry-proteins query_proteins.fasta \\
         --output results/deep_clusters.tsv \\
         --params "--memory-limit 128G --member-cover 60"

  5. Recluster to fix errors:
     python run_clustering.py \\
         --workflow recluster \\
         --database ref \\
         --ref-proteins reference_proteins.fasta \\
         --clusters results/initial_clusters.tsv \\
         --output results/fixed_clusters.tsv \\
         --params "--approx-id 90"

  6. Realign sequences to representatives:
     python run_clustering.py \\
         --workflow realign \\
         --database ref \\
         --ref-proteins reference_proteins.fasta \\
         --clusters results/clusters.tsv \\
         --output results/alignments.tsv \\
         --params "--outfmt 6"
        """
    )

    # Required arguments
    parser.add_argument(
        '--workflow',
        type=str,
        required=True,
        choices=['linclust', 'cluster', 'deepclust', 'recluster', 'realign'],
        help='Clustering workflow to run'
    )

    parser.add_argument(
        '--database', '-d',
        type=str,
        required=True,
        choices=['ref', 'qry', 'all'],
        help='Database to cluster: ref (reference only), qry (query only), all (combined with renamed IDs)'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        required=True,
        help='Output file path'
    )

    # Input files
    parser.add_argument(
        '--ref-proteins',
        type=str,
        help='Reference protein FASTA file (required for ref/all databases)'
    )

    parser.add_argument(
        '--qry-proteins',
        type=str,
        help='Query protein FASTA file (required for qry/all databases)'
    )

    parser.add_argument(
        '--clusters',
        type=str,
        help='Previous clustering output (required for recluster/realign workflows)'
    )

    # Options
    parser.add_argument(
        '--threads',
        type=int,
        default=28,
        help='Number of CPU threads (default: 28)'
    )

    parser.add_argument(
        '--params',
        type=str,
        help='Additional DIAMOND parameters as space-separated string. '
             'Example: "--memory-limit 64G --approx-id 90 --member-cover 80"'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    return parser.parse_args()


def validate_arguments(args):
    """
    Validate command-line arguments.

    Args:
        args: Parsed arguments

    Raises:
        ValueError: If arguments are invalid
    """
    # Check database requirements
    if args.database == 'ref' and not args.ref_proteins:
        raise ValueError("--ref-proteins required when using --database ref")

    if args.database == 'qry' and not args.qry_proteins:
        raise ValueError("--qry-proteins required when using --database qry")

    if args.database == 'all':
        if not args.ref_proteins or not args.qry_proteins:
            raise ValueError("Both --ref-proteins and --qry-proteins required when using --database all")

    # Check workflow-specific requirements
    if args.workflow in ['recluster', 'realign'] and not args.clusters:
        raise ValueError(f"--clusters required for {args.workflow} workflow")

    # Check input files exist
    if args.ref_proteins and not os.path.exists(args.ref_proteins):
        raise FileNotFoundError(f"Reference proteins file not found: {args.ref_proteins}")

    if args.qry_proteins and not os.path.exists(args.qry_proteins):
        raise FileNotFoundError(f"Query proteins file not found: {args.qry_proteins}")

    if args.clusters and not os.path.exists(args.clusters):
        raise FileNotFoundError(f"Clusters file not found: {args.clusters}")


def main():
    """Main entry point."""
    args = parse_arguments()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate arguments
    try:
        validate_arguments(args)
    except (ValueError, FileNotFoundError) as e:
        logger.error(f"Argument validation failed: {e}")
        sys.exit(1)

    # Run workflow
    try:
        workflow = ClusteringWorkflow(args)
        workflow.run_workflow()

        logger.info("Clustering workflow completed successfully!")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Clustering workflow failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
