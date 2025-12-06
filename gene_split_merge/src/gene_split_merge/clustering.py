#!/usr/bin/env python3
"""
DIAMOND Clustering Module
==========================
Provides protein sequence clustering functionality using DIAMOND.

Adapted from diamondonpy with enhancements for gene analysis workflows.

Author: Bioinformatics Workflow
Date: 2025-12-06
"""

import subprocess
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ClusterParser:
    """
    Parse and process DIAMOND clustering output using Union-Find data structure.
    """

    class UnionFind:
        """
        UnionFind (Disjoint Set) data structure for efficient clustering.
        Implements path compression for optimal performance.
        """

        def __init__(self) -> None:
            self.parent: Dict[str, str] = {}
            self.rank: Dict[str, int] = {}

        def find(self, item: str) -> str:
            """
            Find the representative (root) of the set containing item.
            Uses path compression for efficiency.

            Args:
                item: Sequence identifier

            Returns:
                Representative sequence ID
            """
            if item not in self.parent:
                self.parent[item] = item
                self.rank[item] = 0

            if self.parent[item] != item:
                # Path compression
                self.parent[item] = self.find(self.parent[item])

            return self.parent[item]

        def union(self, item1: str, item2: str) -> None:
            """
            Merge the sets containing item1 and item2.
            Uses union by rank for efficiency.

            Args:
                item1: First sequence identifier
                item2: Second sequence identifier
            """
            root1 = self.find(item1)
            root2 = self.find(item2)

            if root1 == root2:
                return

            # Union by rank
            if self.rank[root1] < self.rank[root2]:
                self.parent[root1] = root2
            else:
                self.parent[root2] = root1
                if self.rank[root1] == self.rank[root2]:
                    self.rank[root1] += 1

    @staticmethod
    def parse_clusters(data: str) -> pd.DataFrame:
        """
        Parse cluster data from DIAMOND output.

        DIAMOND clustering produces 2-column TSV output:
        - Column 1: Representative sequence ID
        - Column 2: Member sequence ID

        Args:
            data (str): Raw clustering output from DIAMOND

        Returns:
            pd.DataFrame: DataFrame with columns:
                - cluster_number: Unique identifier for each cluster
                - sequence_id: Sequence identifier
                - representative: Representative sequence for the cluster
                - cluster_size: Number of sequences in the cluster
        """
        uf = ClusterParser.UnionFind()

        # Process each line and build clusters
        for line in data.strip().split('\n'):
            if not line or line.startswith('#'):
                continue

            parts = line.strip().split('\t')
            if len(parts) < 2:
                continue

            representative, member = parts[0], parts[1]
            uf.union(representative, member)

        # Map IDs to their representatives
        id_to_rep: Dict[str, str] = {
            id_: uf.find(id_) for id_ in uf.parent
        }

        # Group IDs by representative
        rep_to_ids: Dict[str, List[str]] = defaultdict(list)
        for id_, rep in id_to_rep.items():
            rep_to_ids[rep].append(id_)

        # Build cluster data
        cluster_data = []
        for cluster_num, (rep, members) in enumerate(sorted(rep_to_ids.items()), 1):
            cluster_size = len(members)
            for seq_id in sorted(members):
                cluster_data.append({
                    'cluster_number': cluster_num,
                    'sequence_id': seq_id,
                    'representative': rep,
                    'cluster_size': cluster_size
                })

        return pd.DataFrame(cluster_data)


class DiamondClusterer:
    """
    DIAMOND clustering wrapper for protein sequences.

    Provides three clustering algorithms:
    - linclust: Fast, linear-time clustering (recommended for >50% identity)
    - cluster: Standard all-vs-all alignment (more sensitive)
    - deepclust: Deep clustering (no identity cutoff, tree-of-life scale)
    """

    def __init__(self, executable: str = "diamond"):
        """
        Initialize the DIAMOND clusterer.

        Args:
            executable: Path to the diamond executable
        """
        self.executable = executable
        self._verify_installation()

    def _verify_installation(self) -> None:
        """Verify that DIAMOND is installed and accessible."""
        try:
            result = subprocess.run(
                [self.executable, '--version'],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"DIAMOND version: {result.stdout.strip()}")
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            raise RuntimeError(
                f"DIAMOND executable not found or not working at {self.executable}. "
                "Please ensure DIAMOND is installed and accessible."
            ) from e

    def linclust(self,
                 input_file: str,
                 output_file: str,
                 approx_id: float = 90.0,
                 member_cover: float = 80.0,
                 threads: int = 28,
                 memory_limit: Optional[str] = None,
                 **kwargs) -> pd.DataFrame:
        """
        Fast linear-time clustering (recommended for large datasets at >50% identity).

        Args:
            input_file: Input FASTA or DIAMOND database file
            output_file: Output file for clustering results
            approx_id: Approximate identity threshold (default: 90%)
            member_cover: Minimum coverage of member by representative (default: 80%)
            threads: Number of CPU threads (default: 28)
            memory_limit: Memory limit (e.g., "64G", strongly recommended)
            **kwargs: Additional DIAMOND options

        Returns:
            DataFrame with parsed clustering results
        """
        logger.info(f"Running DIAMOND linclust on {input_file}")

        cmd = [
            self.executable, 'linclust',
            '-d', input_file,
            '-o', output_file,
            '--approx-id', str(approx_id),
            '--member-cover', str(member_cover),
            '--threads', str(threads)
        ]

        if memory_limit:
            cmd.extend(['-M', memory_limit])

        # Add any additional options
        for key, value in kwargs.items():
            cmd.append(f'--{key.replace("_", "-")}')
            if value is not True:  # Skip value for boolean flags
                cmd.append(str(value))

        self._run_command(cmd)

        # Parse results
        with open(output_file, 'r') as f:
            data = f.read()

        df = ClusterParser.parse_clusters(data)
        logger.info(f"Clustered into {df['cluster_number'].nunique()} clusters")

        return df

    def cluster(self,
                input_file: str,
                output_file: str,
                approx_id: float = 50.0,
                member_cover: float = 80.0,
                threads: int = 28,
                memory_limit: Optional[str] = None,
                **kwargs) -> pd.DataFrame:
        """
        Standard all-vs-all alignment clustering (more sensitive than linclust).

        Args:
            input_file: Input FASTA or DIAMOND database file
            output_file: Output file for clustering results
            approx_id: Approximate identity threshold (default: 50%)
            member_cover: Minimum coverage of member by representative (default: 80%)
            threads: Number of CPU threads (default: 28)
            memory_limit: Memory limit (e.g., "64G", strongly recommended)
            **kwargs: Additional DIAMOND options

        Returns:
            DataFrame with parsed clustering results
        """
        logger.info(f"Running DIAMOND cluster on {input_file}")

        cmd = [
            self.executable, 'cluster',
            '-d', input_file,
            '-o', output_file,
            '--approx-id', str(approx_id),
            '--member-cover', str(member_cover),
            '--threads', str(threads)
        ]

        if memory_limit:
            cmd.extend(['-M', memory_limit])

        # Add any additional options
        for key, value in kwargs.items():
            cmd.append(f'--{key.replace("_", "-")}')
            if value is not True:
                cmd.append(str(value))

        self._run_command(cmd)

        # Parse results
        with open(output_file, 'r') as f:
            data = f.read()

        df = ClusterParser.parse_clusters(data)
        logger.info(f"Clustered into {df['cluster_number'].nunique()} clusters")

        return df

    def deepclust(self,
                  input_file: str,
                  output_file: str,
                  member_cover: float = 80.0,
                  threads: int = 28,
                  memory_limit: Optional[str] = None,
                  **kwargs) -> pd.DataFrame:
        """
        Deep clustering with no identity cutoff (tree-of-life scale).

        Args:
            input_file: Input FASTA or DIAMOND database file
            output_file: Output file for clustering results
            member_cover: Minimum coverage of member by representative (default: 80%)
            threads: Number of CPU threads (default: 28)
            memory_limit: Memory limit (e.g., "64G", strongly recommended)
            **kwargs: Additional DIAMOND options

        Returns:
            DataFrame with parsed clustering results
        """
        logger.info(f"Running DIAMOND deepclust on {input_file}")

        cmd = [
            self.executable, 'deepclust',
            '-d', input_file,
            '-o', output_file,
            '--member-cover', str(member_cover),
            '--threads', str(threads)
        ]

        if memory_limit:
            cmd.extend(['-M', memory_limit])

        # Add any additional options
        for key, value in kwargs.items():
            cmd.append(f'--{key.replace("_", "-")}')
            if value is not True:
                cmd.append(str(value))

        self._run_command(cmd)

        # Parse results
        with open(output_file, 'r') as f:
            data = f.read()

        df = ClusterParser.parse_clusters(data)
        logger.info(f"Clustered into {df['cluster_number'].nunique()} clusters")

        return df

    def recluster(self,
                  input_file: str,
                  clusters_file: str,
                  output_file: str,
                  approx_id: float = 50.0,
                  member_cover: float = 80.0,
                  threads: int = 28,
                  **kwargs) -> pd.DataFrame:
        """
        Fix clustering errors where members don't satisfy criterion against representative.

        Args:
            input_file: Input FASTA or DIAMOND database file
            clusters_file: Previous clustering output (2-column TSV)
            output_file: Output file for corrected clustering
            approx_id: Approximate identity threshold
            member_cover: Minimum coverage threshold
            threads: Number of CPU threads
            **kwargs: Additional DIAMOND options

        Returns:
            DataFrame with corrected clustering results
        """
        logger.info(f"Reclustering to fix errors in {clusters_file}")

        cmd = [
            self.executable, 'recluster',
            '-d', input_file,
            '--clusters', clusters_file,
            '-o', output_file,
            '--approx-id', str(approx_id),
            '--member-cover', str(member_cover),
            '--threads', str(threads)
        ]

        # Add any additional options
        for key, value in kwargs.items():
            cmd.append(f'--{key.replace("_", "-")}')
            if value is not True:
                cmd.append(str(value))

        self._run_command(cmd)

        # Parse results
        with open(output_file, 'r') as f:
            data = f.read()

        df = ClusterParser.parse_clusters(data)
        logger.info(f"Reclustered into {df['cluster_number'].nunique()} clusters")

        return df

    def _run_command(self, cmd: List[str]) -> None:
        """
        Run a DIAMOND command.

        Args:
            cmd: Command as list of strings

        Raises:
            RuntimeError: If command fails
        """
        logger.debug(f"Running command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            if result.stdout:
                logger.debug(f"DIAMOND output: {result.stdout}")

        except subprocess.CalledProcessError as e:
            error_msg = f"DIAMOND command failed: {' '.join(cmd)}\n"
            if e.stderr:
                error_msg += f"Error: {e.stderr}\n"
            if e.stdout:
                error_msg += f"Output: {e.stdout}\n"

            raise RuntimeError(error_msg) from e

    @staticmethod
    def get_cluster_representatives(df: pd.DataFrame) -> List[str]:
        """
        Extract list of cluster representatives from clustering DataFrame.

        Args:
            df: Clustering DataFrame from parse_clusters

        Returns:
            List of representative sequence IDs
        """
        return df['representative'].unique().tolist()

    @staticmethod
    def get_cluster_members(df: pd.DataFrame, representative: str) -> List[str]:
        """
        Get all members of a cluster by its representative.

        Args:
            df: Clustering DataFrame
            representative: Representative sequence ID

        Returns:
            List of member sequence IDs
        """
        cluster_df = df[df['representative'] == representative]
        return cluster_df['sequence_id'].tolist()

    @staticmethod
    def get_cluster_stats(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate statistics for each cluster.

        Args:
            df: Clustering DataFrame

        Returns:
            DataFrame with cluster statistics:
                - cluster_number
                - representative
                - size
                - members (comma-separated)
        """
        stats = df.groupby(['cluster_number', 'representative']).agg(
            size=('sequence_id', 'count'),
            members=('sequence_id', lambda x: ','.join(sorted(x)))
        ).reset_index()

        return stats.sort_values('size', ascending=False)


def main():
    """Example usage of DIAMOND clustering."""
    print("DIAMOND Clustering Module")
    print("=" * 60)
    print("\nThis module provides protein sequence clustering using DIAMOND.")
    print("\nExample usage:")
    print("""
from .clustering import DiamondClusterer

# Initialize clusterer
clusterer = DiamondClusterer()

# Fast clustering for redundancy removal (90% identity)
df = clusterer.linclust(
    input_file="proteins.fasta",
    output_file="clusters_90.tsv",
    approx_id=90.0,
    member_cover=80.0,
    threads=28,
    memory_limit="64G"
)

# Get cluster statistics
stats = DiamondClusterer.get_cluster_stats(df)
print(stats.head())

# Extract representatives
representatives = DiamondClusterer.get_cluster_representatives(df)
print(f"Number of representative sequences: {len(representatives)}")
    """)
    print("=" * 60)


if __name__ == '__main__':
    main()
