#!/usr/bin/env python3
"""
InterProScan Output Parser
Parses InterProScan output files (TSV, XML, JSON, GFF3) and optionally runs InterProScan.
"""

import argparse
import subprocess
import sys
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict


class InterProParser:
    """Parser for InterProScan output files"""

    def __init__(self):
        self.data = []
        self.domain_lengths = defaultdict(list)
        self.pathway_annotations = {}  # Store pathway annotations for future use

    def parse_tsv(self, filepath: str) -> List[Dict]:
        """
        Parse TSV format InterProScan output (15-column format).

        Standard InterProScan TSV is always 15 columns:
        - Columns 1-13: Core annotation data
        - Column 14: GO terms
        - Column 15: Pathway annotations

        Missing values are represented as "-" (dash) and are converted to empty strings.

        Args:
            filepath: Path to TSV file

        Returns:
            List of dictionaries containing parsed data

        Note:
            - Pathway annotations are stored internally in self.pathway_annotations but excluded from output TSV
            - GO annotations are included in output TSV if present (non-empty)
        """
        results = []

        with open(filepath, 'r') as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue

                fields = line.strip().split('\t')

                # InterProScan outputs 15 columns (older versions may have 11-13)
                if len(fields) < 11:
                    continue

                # Helper function to handle dash values
                def parse_field(field, default=''):
                    return '' if field == '-' else field

                entry = {
                    'protein_accession': fields[0],
                    'md5_digest': parse_field(fields[1]),
                    'sequence_length': int(fields[2]),
                    'analysis': fields[3],
                    'signature_accession': fields[4],
                    'signature_description': parse_field(fields[5] if len(fields) > 5 else ''),
                    'start_location': int(fields[6]),
                    'stop_location': int(fields[7]),
                    'score': parse_field(fields[8]),
                    'status': parse_field(fields[9]),
                    'date': parse_field(fields[10]),
                    'interpro_accession': parse_field(fields[11] if len(fields) > 11 else ''),
                    'interpro_description': parse_field(fields[12] if len(fields) > 12 else ''),
                }

                # Parse GO annotations (column 14) - always present in 15-column format
                if len(fields) > 13:
                    go_value = parse_field(fields[13])
                    if go_value:
                        entry['go_annotations'] = go_value

                # Parse pathway annotations (column 15) - always present in 15-column format
                # Store internally only, not included in output TSV
                if len(fields) > 14:
                    pathway_value = parse_field(fields[14])
                    if pathway_value:
                        protein_acc = entry['protein_accession']
                        signature_acc = entry['signature_accession']

                        # Store in internal dictionary for future use
                        key = f"{protein_acc}_{signature_acc}"
                        if key not in self.pathway_annotations:
                            self.pathway_annotations[key] = pathway_value

                results.append(entry)

        self.data = results
        return results

    def parse_gff3(self, filepath: str) -> List[Dict]:
        """
        Parse GFF3 format InterProScan output.

        Args:
            filepath: Path to GFF3 file

        Returns:
            List of dictionaries containing parsed data
        """
        results = []

        with open(filepath, 'r') as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue

                fields = line.strip().split('\t')

                if len(fields) < 9:
                    continue

                # Parse attributes column
                attributes = {}
                for attr in fields[8].split(';'):
                    if '=' in attr:
                        key, value = attr.split('=', 1)
                        attributes[key] = value

                entry = {
                    'protein_accession': fields[0],
                    'source': fields[1],
                    'feature_type': fields[2],
                    'start_location': int(fields[3]),
                    'stop_location': int(fields[4]),
                    'score': fields[5],
                    'strand': fields[6],
                    'phase': fields[7],
                    'attributes': attributes
                }

                results.append(entry)

        self.data = results
        return results

    def parse_xml(self, filepath: str) -> List[Dict]:
        """
        Parse XML format InterProScan output.

        Args:
            filepath: Path to XML file

        Returns:
            List of dictionaries containing parsed data
        """
        results = []

        try:
            tree = ET.parse(filepath)
            root = tree.getroot()

            # Handle different XML structures
            # This is a basic implementation - adjust based on actual XML structure
            for protein in root.findall('.//protein'):
                protein_acc = protein.get('id', '')

                for match in protein.findall('.//match'):
                    entry = {
                        'protein_accession': protein_acc,
                        'signature_accession': match.get('id', ''),
                        'signature_description': match.get('name', ''),
                    }

                    # Extract location information
                    for location in match.findall('.//location'):
                        entry['start_location'] = int(location.get('start', 0))
                        entry['stop_location'] = int(location.get('end', 0))
                        entry['score'] = location.get('score', '')

                    results.append(entry)

        except ET.ParseError as e:
            print(f"Error parsing XML file: {e}", file=sys.stderr)
            return []

        self.data = results
        return results

    def parse_json(self, filepath: str) -> List[Dict]:
        """
        Parse JSON format InterProScan output.

        Args:
            filepath: Path to JSON file

        Returns:
            List of dictionaries containing parsed data
        """
        results = []

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            # Handle different JSON structures
            # Adjust based on actual JSON structure
            if isinstance(data, dict) and 'results' in data:
                data = data['results']

            if isinstance(data, list):
                for entry in data:
                    if isinstance(entry, dict):
                        # Extract relevant fields
                        parsed_entry = {
                            'protein_accession': entry.get('xref', [{}])[0].get('id', '') if entry.get('xref') else '',
                            'sequence_length': entry.get('sequence-length', 0),
                        }

                        # Extract matches
                        for match in entry.get('matches', []):
                            match_entry = parsed_entry.copy()
                            match_entry['signature_accession'] = match.get('signature', {}).get('accession', '')
                            match_entry['signature_description'] = match.get('signature', {}).get('name', '')

                            # Extract locations
                            for location in match.get('locations', []):
                                loc_entry = match_entry.copy()
                                loc_entry['start_location'] = location.get('start', 0)
                                loc_entry['stop_location'] = location.get('end', 0)
                                loc_entry['score'] = location.get('score', '')
                                results.append(loc_entry)

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON file: {e}", file=sys.stderr)
            return []

        self.data = results
        return results

    def longest_domain(self) -> Tuple[List[Dict], Dict]:
        """
        Select proteins with longest domain when multiple domains match.

        Returns:
            Tuple of (filtered_results, domain_length_distribution)
            - filtered_results: List with only longest domain per protein
            - domain_length_distribution: Dict mapping protein to list of domain info
        """
        # Group by protein accession
        protein_domains = defaultdict(list)

        for entry in self.data:
            protein_acc = entry.get('protein_accession', '')
            if not protein_acc:
                continue

            # Calculate domain coverage
            start = entry.get('start_location', 0)
            stop = entry.get('stop_location', 0)
            domain_length = stop - start + 1

            domain_info = {
                'domain_name': entry.get('signature_description', entry.get('signature_accession', '')),
                'length': domain_length,
                'score': entry.get('score', ''),
                'start': start,
                'stop': stop,
                'entry': entry
            }

            protein_domains[protein_acc].append(domain_info)

        # Select longest domain for each protein
        longest_results = []
        domain_length_dist = {}

        for protein_acc, domains in protein_domains.items():
            # Sort by length (descending)
            sorted_domains = sorted(domains, key=lambda x: x['length'], reverse=True)

            # Keep the longest domain
            longest_results.append(sorted_domains[0]['entry'])

            # Store all domain lengths for this protein
            domain_length_dist[protein_acc] = [
                {
                    'domain': d['domain_name'],
                    'length': d['length'],
                    'score': d['score'],
                    'start': d['start'],
                    'stop': d['stop']
                }
                for d in sorted_domains
            ]

        return longest_results, domain_length_dist

    def longest_interpro_domain(self) -> Tuple[List[Dict], Dict]:
        """
        Select proteins with longest InterPro-annotated domain (IPR prefix).
        Only considers domains with interpro_accession starting with 'IPR'.

        Returns:
            Tuple of (filtered_results, domain_length_distribution)
            - filtered_results: List with only longest InterPro domain per protein
            - domain_length_distribution: Dict mapping protein to list of InterPro domain info
        """
        # Group by protein accession, filter only InterPro annotated domains
        protein_interpro_domains = defaultdict(list)

        for entry in self.data:
            protein_acc = entry.get('protein_accession', '')
            interpro_acc = entry.get('interpro_accession', '')

            if not protein_acc:
                continue

            # Only include entries with InterPro annotation (IPR prefix)
            if not interpro_acc or not interpro_acc.startswith('IPR'):
                continue

            # Calculate domain coverage
            start = entry.get('start_location', 0)
            stop = entry.get('stop_location', 0)
            domain_length = stop - start + 1

            domain_info = {
                'domain_name': entry.get('signature_description', entry.get('signature_accession', '')),
                'interpro_accession': interpro_acc,
                'interpro_description': entry.get('interpro_description', ''),
                'length': domain_length,
                'score': entry.get('score', ''),
                'start': start,
                'stop': stop,
                'entry': entry
            }

            protein_interpro_domains[protein_acc].append(domain_info)

        # Select longest InterPro domain for each protein
        longest_interpro_results = []
        interpro_domain_length_dist = {}

        for protein_acc, domains in protein_interpro_domains.items():
            # Sort by length (descending)
            sorted_domains = sorted(domains, key=lambda x: x['length'], reverse=True)

            # Keep the longest InterPro domain
            longest_interpro_results.append(sorted_domains[0]['entry'])

            # Store all InterPro domain lengths for this protein
            interpro_domain_length_dist[protein_acc] = [
                {
                    'domain': d['domain_name'],
                    'interpro_accession': d['interpro_accession'],
                    'interpro_description': d['interpro_description'],
                    'length': d['length'],
                    'score': d['score'],
                    'start': d['start'],
                    'stop': d['stop']
                }
                for d in sorted_domains
            ]

        return longest_interpro_results, interpro_domain_length_dist


def write_longest_results_tsv(results: List[Dict], filepath: str):
    """
    Write longest domain results to TSV file in 14-column format.

    Output format is 13-14 columns:
    - Columns 1-13: Standard InterProScan fields
    - Column 14: GO annotations (included if present in data)
    - Pathway annotations (column 15) are EXCLUDED from output

    Args:
        results: List of result dictionaries
        filepath: Output TSV file path

    Note:
        - Pathway annotations are excluded from TSV output but stored internally
        - GO annotations are included if present in the entry dictionary
    """
    with open(filepath, 'w') as f:
        for entry in results:
            # Columns 1-13: Standard fields
            row = [
                str(entry.get('protein_accession', '')),
                str(entry.get('md5_digest', '')),
                str(entry.get('sequence_length', '')),
                str(entry.get('analysis', '')),
                str(entry.get('signature_accession', '')),
                str(entry.get('signature_description', '')),
                str(entry.get('start_location', '')),
                str(entry.get('stop_location', '')),
                str(entry.get('score', '')),
                str(entry.get('status', '')),
                str(entry.get('date', '')),
                str(entry.get('interpro_accession', '')),
                str(entry.get('interpro_description', '')),
            ]

            # Column 14: GO annotations (only if present in entry)
            if 'go_annotations' in entry and entry['go_annotations']:
                row.append(str(entry['go_annotations']))

            # NOTE: Pathway annotations (column 15) are intentionally excluded from output
            # They are stored in InterProParser.pathway_annotations for future use

            f.write('\t'.join(row) + '\n')


def write_domain_stats_tsv(domain_stats: Dict, filepath: str):
    """
    Write domain length distribution to TSV file.

    Args:
        domain_stats: Dictionary mapping protein to list of domain info
        filepath: Output TSV file path
    """
    with open(filepath, 'w') as f:
        # Write header
        f.write('protein_accession\tdomain_name\tdomain_length\tscore\tstart\tstop\trank\n')

        for protein_acc, domains in sorted(domain_stats.items()):
            for rank, domain in enumerate(domains, start=1):
                row = [
                    str(protein_acc),
                    str(domain['domain']),
                    str(domain['length']),
                    str(domain['score']),
                    str(domain['start']),
                    str(domain['stop']),
                    str(rank)
                ]
                f.write('\t'.join(row) + '\n')


def generate_default_filename(input_file: str, suffix: str, extension: str) -> str:
    """
    Generate default output filename based on input filename.

    Args:
        input_file: Input file path
        suffix: Descriptive suffix (e.g., 'parsed', 'longest_domains', 'domain_distribution')
        extension: File extension (e.g., 'json', 'tsv')

    Returns:
        Generated filename: basename_suffix.extension
    """
    input_path = Path(input_file)
    basename = input_path.stem  # Filename without extension
    return f"{basename}_{suffix}.{extension}"


def run_interproscan(
    protein_file: str,
    cpu: int,
    output_file: str,
    output_format: str,
    goterms: bool = False,
    pathways: bool = False,
    search_term: Optional[str] = None,
    databases: Optional[str] = None
) -> bool:
    """
    Run InterProScan on protein sequences.

    Args:
        protein_file: Input FASTA file with protein sequences
        cpu: Number of CPUs to use
        output_file: Output file name
        output_format: Output format (TSV, XML, JSON, GFF3)
        goterms: Include GO term annotations
        pathways: Include pathway annotations
        search_term: Optional search term filter
        databases: Databases to search (Option and default to all if unset, or comma-separated list)

    Returns:
        True if successful, False otherwise
    """
    cmd = [
        'interproscan.sh',
        '-i', protein_file,
        '-cpu', str(cpu),
        '-o', output_file,
        '-f', output_format
    ]

    if goterms:
        cmd.append('-goterms')

    if pathways:
        cmd.append('-pathways')

    if databases:
        cmd.extend(['-appl', databases])

    print(f"Running InterProScan: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("InterProScan completed successfully")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running InterProScan: {e}", file=sys.stderr)
        print(f"STDERR: {e.stderr}", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("Error: interproscan.sh not found. Please ensure InterProScan is installed and in PATH.", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Parse InterProScan output or run InterProScan and parse results'
    )

    # Mode selection
    parser.add_argument(
        '--run',
        action='store_true',
        help='Run InterProScan before parsing'
    )

    # InterProScan run arguments
    parser.add_argument(
        '-i', '--input',
        help='Input protein FASTA file (required if --run is used)'
    )
    parser.add_argument(
        '--cpu',
        type=int,
        default=4,
        help='Number of CPUs to use for InterProScan (default: 4)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output file name (required if --run is used)'
    )
    parser.add_argument(
        '-f', '--format',
        choices=['TSV', 'XML', 'JSON', 'GFF3', 'tsv', 'xml', 'json', 'gff3'],
        default='TSV',
        help='Output format (default: TSV)'
    )
    parser.add_argument(
        '--goterms',
        action='store_true',
        help='Include GO term annotations'
    )
    parser.add_argument(
        '--pathways',
        action='store_true',
        help='Include pathway annotations'
    )
    parser.add_argument(
        '--databases',
        # default='all',
        help='Databases to search (default to all if unset, or comma-separated list)'
    )

    # Parsing arguments
    parser.add_argument(
        '--parse',
        help='InterProScan output file to parse (format auto-detected from file extension)'
    )

    # Analysis options
    parser.add_argument(
        '--longest-domain',
        action='store_true',
        help='Select only the longest domain for each protein'
    )
    parser.add_argument(
        '--domain-stats',
        help='Output file for domain length distribution statistics (JSON). If not specified, defaults to <input>_domain_distribution.json'
    )
    parser.add_argument(
        '--domain-stats-tsv',
        help='Output file for domain length distribution statistics (TSV). If not specified, defaults to <input>_domain_distribution.tsv'
    )
    parser.add_argument(
        '--output-parsed',
        help='Output file for parsed results (JSON). If not specified, defaults to <input>_parsed.json'
    )
    parser.add_argument(
        '--output-parsed-tsv',
        help='Output file for parsed results (TSV). If not specified, defaults to <input>_parsed.tsv'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.run:
        if not args.input or not args.output:
            parser.error("--run requires --input and --output arguments")

        # Run InterProScan
        success = run_interproscan(
            protein_file=args.input,
            cpu=args.cpu,
            output_file=args.output,
            output_format=args.format,
            goterms=args.goterms,
            pathways=args.pathways,
            databases=args.databases
        )

        if not success:
            sys.exit(1)

        # Set parse file to the output
        parse_file = args.output
        parse_format = args.format.upper()

    elif args.parse:
        parse_file = args.parse

        # Auto-detect format from file extension
        ext = Path(parse_file).suffix.lower()
        format_map = {
            '.tsv': 'TSV',
            '.txt': 'TSV',
            '.xml': 'XML',
            '.json': 'JSON',
            '.gff3': 'GFF3',
            '.gff': 'GFF3'
        }
        parse_format = format_map.get(ext, 'TSV')
        print(f"Auto-detected format from extension '{ext}': {parse_format}")

    else:
        parser.error("Either --run or --parse must be specified")

    # Parse the file
    print(f"Parsing {parse_format} file: {parse_file}")
    interpro = InterProParser()

    if parse_format == 'TSV':
        results = interpro.parse_tsv(parse_file)
    elif parse_format == 'GFF3':
        results = interpro.parse_gff3(parse_file)
    elif parse_format == 'XML':
        results = interpro.parse_xml(parse_file)
    elif parse_format == 'JSON':
        results = interpro.parse_json(parse_file)
    else:
        print(f"Unsupported format: {parse_format}", file=sys.stderr)
        sys.exit(1)

    print(f"Parsed {len(results)} entries")

    # Apply longest domain filter if requested
    domain_stats = None
    interpro_domain_stats = None
    interpro_results = None

    if args.longest_domain:
        print("Selecting longest domain for each protein...")
        results, domain_stats = interpro.longest_domain()
        print(f"Filtered to {len(results)} entries (one per protein)")

        # Also get longest InterPro-annotated domain
        print("Selecting longest InterPro-annotated domain for each protein...")
        interpro_results, interpro_domain_stats = interpro.longest_interpro_domain()
        if interpro_results:
            print(f"Filtered to {len(interpro_results)} entries with InterPro annotation (IPR prefix)")
        else:
            print("No InterPro-annotated domains found (no entries with IPR prefix)")

    # Determine if any output is needed
    output_any = args.domain_stats or args.domain_stats_tsv or args.output_parsed or args.output_parsed_tsv

    # Save domain statistics if requested or if longest_domain was used
    if domain_stats:
        # Generate default filenames if not specified
        if args.longest_domain and not output_any:
            # Auto-generate all outputs when --longest-domain is used without explicit outputs
            domain_stats_json = generate_default_filename(parse_file, 'domain_distribution', 'json')
            domain_stats_tsv = generate_default_filename(parse_file, 'domain_distribution', 'tsv')
            output_parsed_json = generate_default_filename(parse_file, 'longest_domains', 'json')
            output_parsed_tsv = generate_default_filename(parse_file, 'longest_domains', 'tsv')

            # Save domain statistics (JSON)
            with open(domain_stats_json, 'w') as f:
                json.dump(domain_stats, f, indent=2)
            print(f"Domain statistics (JSON) saved to {domain_stats_json}")

            # Save domain statistics (TSV)
            write_domain_stats_tsv(domain_stats, domain_stats_tsv)
            print(f"Domain statistics (TSV) saved to {domain_stats_tsv}")

            # Save parsed results (JSON)
            with open(output_parsed_json, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Longest domains (JSON) saved to {output_parsed_json}")

            # Save parsed results (TSV)
            write_longest_results_tsv(results, output_parsed_tsv)
            print(f"Longest domains (TSV) saved to {output_parsed_tsv}")

            # Save InterPro-annotated results if available
            if interpro_results and interpro_domain_stats:
                interpro_domain_stats_json = generate_default_filename(parse_file, 'domain_distribution_NotintAnn', 'json')
                interpro_domain_stats_tsv = generate_default_filename(parse_file, 'domain_distribution_NotintAnn', 'tsv')
                interpro_output_parsed_json = generate_default_filename(parse_file, 'longest_domains_NotintAnn', 'json')
                interpro_output_parsed_tsv = generate_default_filename(parse_file, 'longest_domains_NotintAnn', 'tsv')

                # Save InterPro domain statistics (JSON)
                with open(interpro_domain_stats_json, 'w') as f:
                    json.dump(interpro_domain_stats, f, indent=2)
                print(f"InterPro domain statistics (JSON) saved to {interpro_domain_stats_json}")

                # Save InterPro domain statistics (TSV)
                write_domain_stats_tsv(interpro_domain_stats, interpro_domain_stats_tsv)
                print(f"InterPro domain statistics (TSV) saved to {interpro_domain_stats_tsv}")

                # Save InterPro parsed results (JSON)
                with open(interpro_output_parsed_json, 'w') as f:
                    json.dump(interpro_results, f, indent=2)
                print(f"Longest InterPro domains (JSON) saved to {interpro_output_parsed_json}")

                # Save InterPro parsed results (TSV)
                write_longest_results_tsv(interpro_results, interpro_output_parsed_tsv)
                print(f"Longest InterPro domains (TSV) saved to {interpro_output_parsed_tsv}")
        else:
            # User specified some outputs explicitly
            if args.domain_stats:
                with open(args.domain_stats, 'w') as f:
                    json.dump(domain_stats, f, indent=2)
                print(f"Domain statistics (JSON) saved to {args.domain_stats}")

            if args.domain_stats_tsv:
                write_domain_stats_tsv(domain_stats, args.domain_stats_tsv)
                print(f"Domain statistics (TSV) saved to {args.domain_stats_tsv}")

    # Save parsed results if requested
    if args.output_parsed:
        with open(args.output_parsed, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Parsed results (JSON) saved to {args.output_parsed}")

    if args.output_parsed_tsv:
        write_longest_results_tsv(results, args.output_parsed_tsv)
        print(f"Parsed results (TSV) saved to {args.output_parsed_tsv}")
    elif not args.longest_domain and not output_any:
        # Auto-generate parsed output (TSV) when no specific output requested and no longest_domain
        output_parsed_tsv = generate_default_filename(parse_file, 'parsed', 'tsv')
        write_longest_results_tsv(results, output_parsed_tsv)
        print(f"Parsed results (TSV) saved to {output_parsed_tsv}")

    # Print summary
    print("\nSummary:")
    print(f"Total entries: {len(results)}")

    if results:
        # Count unique proteins
        unique_proteins = set(r.get('protein_accession', '') for r in results)
        print(f"Unique proteins: {len(unique_proteins)}")

        # Count analyses/databases
        analyses = defaultdict(int)
        for r in results:
            analysis = r.get('analysis', r.get('source', 'Unknown'))
            analyses[analysis] += 1

        print("\nMatches by database:")
        for analysis, count in sorted(analyses.items(), key=lambda x: x[1], reverse=True):
            print(f"  {analysis}: {count}")


if __name__ == '__main__':
    main()
