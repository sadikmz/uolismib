#!/usr/bin/env python3
"""
PAVprot
"""

from collections import defaultdict
import argparse
import sys
import os
import subprocess
import gzip
import pandas as pd
from pathlib import Path

# Import InterProParser and run_interproscan from same directory
from parse_interproscan import InterProParser, run_interproscan

class PAVprot:
    @staticmethod
    def fasta2dict(source, is_query=False):
        if str(source) == '-':
            lines = sys.stdin
            close_at_end = False
        else:
            lines = open(source, 'r')
            close_at_end = True

        context = lines if not close_at_end else open(source, 'r')

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
    def load_gff(gff_path: str):
        rna_to_protein = {}
        locus_to_gene = {}

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
    def parse_tracking(cls, filepath: str, feature_table: str = None, filter_codes: set = None):
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


    @classmethod
    def filter_multi_transcripts(cls, full_dict: dict):
        
        """
        Assign class_type (for visualization purpose):
            0 → em,c,k,m,n
            1 → em,c,k,m,n,j
            2 → o,e
            3 → s,x
            4 → i,y 
            5 → anything else (p,r,u)
        """
        
        # Step 1: Group entries by query_gene
        query_gene_to_entries = defaultdict(list)
        for entries in full_dict.values():
            for entry in entries:
                query_gene_to_entries[entry['query_gene']].append(entry)
        
        # Step 2: Analyze each query_gene for multiple transcripts
        
        query_gene_info = {}
        
        for qgene, qentries in query_gene_to_entries.items():
            if len(qentries) <=1:
                # Only one transcript - no multi-transcript case
                class_codes = {qentries[0]['class_code']}
            else:
                # Multiple transcripts
                class_codes = {e['class_code'] for e in qentries}
            
            code_str = ';'.join(sorted(class_codes))
            
            # Assign class_type
            if class_codes <= {'em','c','k','m','n'}:
                ctype = '0'
            elif class_codes <= {'em','c','k','m','n','j'}:
                ctype = '1'
            elif class_codes <= {'o','e'}:
                ctype = '2'
            elif class_codes <= {'s','x'}:
                ctype = '3'
            elif class_codes <= {'i','y'}:
                ctype = '4'
            else:
                ctype = '5'

            # Calculate emckmnj: 1 if any code in [em,c,k,m,n,j], else 0
            emckmnj = 1 if class_codes & {'em', 'c', 'k', 'm', 'n', 'j'} else 0

            # Calculate emckmnje: 1 if any code in [em,c,k,m,n,j,e], else 0
            emckmnje = 1 if class_codes & {'em', 'c', 'k', 'm', 'n', 'j', 'e'} else 0

            query_gene_info[qgene] = {
                'class_code_multi': code_str,
                'class_type': ctype,
                'emckmnj': emckmnj,
                'emckmnje': emckmnje
            }
            
        # Step 3: Attach info back to entries
        for entries in full_dict.values():
            for entry in entries:
                qgene = entry['query_gene']
                # if qgene in query_gene_info:
                    # entry.update(query_gene_info[qgene])
                info = query_gene_info.get(qgene, {
                    'class_code_multi': entry['class_code'],
                    'class_type': '3',
                    'emckmnj': 0,
                    'emckmnje': 0
                })
                entry['class_code_multi'] = info['class_code_multi']
                entry['class_type'] = info['class_type']
                entry['emckmnj'] = info['emckmnj']
                entry['emckmnje'] = info['emckmnje']
                
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

            # Get longest IPR domain info
            longest_idx = protein_data['domain_length'].idxmax()
            longest_domain = protein_data.loc[longest_idx]

            # Calculate total IPR domain length (sum of all IPR domains)
            total_length = protein_data['domain_length'].sum()

            result[protein_acc] = {
                'analysis': longest_domain['analysis'],
                'signature_accession': longest_domain['signature_accession'],
                'total_IPR_domain_length': int(total_length)
            }

        return result

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
    def __init__(self, threads: int = 40, output_prefix: str = "synonym_mapping_liftover_gffcomp"):
        self.threads = threads
        self.output_prefix = output_prefix

    def diamond_blastp(self, ref_faa_path: str, qry_faa_path: str) -> str:
        """Run one single all-vs-all DIAMOND blastp"""
        out_dir = os.path.join(os.getcwd(), 'pavprot_out', 'compareprot_out')
        os.makedirs(out_dir, exist_ok=True)
        diamond_out = os.path.join(out_dir, f"{self.output_prefix}_diamond_blastp.tsv.gz")
        
        
        cmd_str = (
            f"diamond blastp "
            f"--db {ref_faa_path} "
            f"--query {qry_faa_path} "
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

        print(f"Running full DIAMOND blastp → {diamond_out}", file=sys.stderr)
        subprocess.run(cmd_str, shell=True, check=True)

        return diamond_out

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
                    entry["identical_aa"] = h["nident"]
                    entry["mismatched_aa"] = h["mismatch"]
                    entry["indels_aa"] = h["gaps"]
                    entry["aligned_aa"] = h["length"]
                else:
                    entry["diamond"] = None
                    entry["identical_aa"] = entry["mismatched_aa"] = entry["indels_aa"] = entry["aligned_aa"] = entry['pident'] = entry['qcovhsp'] = 0
                
                # add pidentCov_9090 info 
                if qid in multi_match_queries:
                    matching_refs = query_to_high_hits[qid]
                    entry['pidentCov_9090'] = {"ref_cnt": len(matching_refs), 
                                               "ref_trans": matching_refs}
                else:
                    entry['pidentCov_9090'] = None

        return data


def main():
    parser = argparse.ArgumentParser(description="PAVprot – complete class-based pipeline")
    parser.add_argument('--gff-comp', required=True)
    parser.add_argument('--gff', help="GFF3 CDS feature table. Single GFF for reference only, or comma-separated 'ref.gff,query.gff' for both")
    parser.add_argument('--liftoff-gff', help="Liftoff GFF3 with extra_copy_number (optional)")
    parser.add_argument('--class-code', help="Comma-separated class codes (e.g. em,j)")
    parser.add_argument('--ref-faa', help="Reference proteins FASTA")
    parser.add_argument('--qry-faa', help="Query proteins FASTA")
    parser.add_argument('--run-diamond', action='store_true')
    parser.add_argument('--diamond-threads', type=int, default=40)
    parser.add_argument('--output-prefix', default="synonym_mapping_liftover_gffcomp")
    parser.add_argument('--interproscan-out', help="InterProScan TSV output file(s). Single file for single GFF, or comma-separated for 2 GFFs. Format: 'ref_interpro.tsv' or 'ref_interpro.tsv,query_interpro.tsv'")

    # InterProScan running options
    parser.add_argument('--run-interproscan', action='store_true', help='Run InterProScan on input protein files before parsing')
    parser.add_argument('--input-prots', help="Comma-separated protein FASTA file(s). Single file for single GFF, or 2 files for 2 GFFs. Format: 'ref.faa' or 'ref.faa,query.faa'")
    parser.add_argument('--interproscan-cpu', type=int, default=4, help='Number of CPUs for InterProScan (default: 4)')
    parser.add_argument('--interproscan-pathways', action='store_true', help='Include pathway annotations in InterProScan')
    parser.add_argument('--interproscan-databases', help='Databases to search (comma-separated, default: all)')

    args = parser.parse_args()

    # Parse ref-gff to check if comma-separated
    ref_gff_list = [g.strip() for g in args.gff.split(',')] if args.gff else []
    num_gffs = len(ref_gff_list)

    # Handle InterProScan running if requested
    if args.run_interproscan:
        if not args.input_prots:
            parser.error("--run-interproscan requires --input-prots argument")

        # Parse input protein files
        input_prot_files = [f.strip() for f in args.input_prots.split(',')]

        # Validate number of protein files matches number of GFFs (if GFF provided)
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

        # Run InterProScan for each protein file
        print("\n" + "="*80, file=sys.stderr)
        print("RUNNING INTERPROSCAN", file=sys.stderr)
        print("="*80, file=sys.stderr)

        # Create pavprot_out directory for all outputs
        pavprot_out = os.path.join(os.getcwd(), 'pavprot_out')
        os.makedirs(pavprot_out, exist_ok=True)

        interproscan_output_files = []
        for i, prot_file in enumerate(input_prot_files):
            file_type = "Reference" if i == 0 else "Query"
            print(f"\n[{i+1}/{len(input_prot_files)}] Running InterProScan for {file_type} proteins: {prot_file}", file=sys.stderr)

            # Generate output basename in pavprot_out directory
            output_basename = Path(prot_file).stem + "_interproscan"
            output_base = os.path.join(pavprot_out, output_basename)

            # Run InterProScan
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

            # Add output file to list
            output_file = f"{output_base}.tsv"
            interproscan_output_files.append(output_file)
            print(f"  → InterProScan output: {output_file}", file=sys.stderr)

        print("\n" + "="*80, file=sys.stderr)
        print("✓ InterProScan completed for all files!", file=sys.stderr)
        print("="*80 + "\n", file=sys.stderr)

        # Set interproscan_files to the generated output files
        interproscan_files = interproscan_output_files

    # Validate interproscan-out based on number of GFFs
    else:
        interproscan_files = []
        if args.interproscan_out:
            interproscan_files = [f.strip() for f in args.interproscan_out.split(',')]

        # Validate number of InterProScan files
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
        elif num_gffs == 0:
            if len(interproscan_files) > 0:
                print(f"Note: {len(interproscan_files)} InterProScan file(s) provided without GFF - protein-level data only (no gene mapping)", file=sys.stderr)

        # Validate files exist
        for f in interproscan_files:
            if not os.path.exists(f):
                parser.error(f"InterProScan file not found: {f}")

    # Use first GFF for parse_tracking (reference GFF)
    ref_gff_for_tracking = ref_gff_list[0] if ref_gff_list else None

    filter_set = {c.strip() for c in args.class_code.split(',')} if args.class_code else None
    full, filtered = PAVprot.parse_tracking(args.gff_comp, ref_gff_for_tracking, filter_set)
    data = filtered if filtered else full

    if args.run_diamond:
        if not args.ref_faa or not args.qry_faa:
            print("Error: --run-diamond requires --ref-faa and --qry-faa", file=sys.stderr)
            sys.exit(1)

        # Prepare input FASTA files
        pavprot_out = os.path.join(os.getcwd(), 'pavprot_out')
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

        diamond = DiamondRunner(threads=args.diamond_threads, output_prefix=args.output_prefix)
        diamond_tsv_gz = diamond.diamond_blastp(ref_faa_path, qry_faa_path)
        data = diamond.enrich_blastp(data, diamond_tsv_gz)
        

    # Apply multi-transcript classification
    data = PAVprot.filter_multi_transcripts(data)

    # Apply extra copy number from Liftoff GFF
    if args.liftoff_gff:
        data = PAVprot.filter_extra_copy_transcripts(data, args.liftoff_gff)

    # Load and enrich with InterProScan data
    has_interproscan = False
    ref_interproscan_map = {}
    qry_interproscan_map = {}

    # Create pavprot_out directory for parse_interproscan outputs
    pavprot_out = os.path.join(os.getcwd(), 'pavprot_out')
    os.makedirs(pavprot_out, exist_ok=True)

    if interproscan_files and len(interproscan_files) > 0:
        print("\n" + "="*80, file=sys.stderr)
        print("RUNNING INTERPROSCAN INTEGRATION (parse_interproscan functionality)", file=sys.stderr)
        print("="*80, file=sys.stderr)

        # Case 1: No GFF - Parse InterProScan without gene mapping
        if num_gffs == 0:
            print(f"\n[1/3] No GFF mode: Protein-level data only (no gene mapping)", file=sys.stderr)
            for i, interpro_file in enumerate(interproscan_files):
                file_type = "Reference" if i == 0 else "Query"
                print(f"  {file_type} InterProScan: {interpro_file}", file=sys.stderr)

            # Parse each InterProScan file without gene mapping
            parsers_list = []
            for i, interpro_file in enumerate(interproscan_files):
                file_type = "Reference" if i == 0 else "Query"
                print(f"\n[{i+2}/{len(interproscan_files)+2}] Parsing {file_type.lower()} InterProScan (protein-level only)...", file=sys.stderr)

                parser = InterProParser(gff_file=None)
                df = parser.parse_tsv(interpro_file)
                print(f"  → Loaded {len(df)} InterProScan entries", file=sys.stderr)
                print(f"  → Calculating total IPR lengths per protein...", file=sys.stderr)

                ipr_map = parser.total_ipr_length()
                print(f"  → Calculated for {len(ipr_map)} proteins (using protein_accession as key)", file=sys.stderr)

                if i == 0:
                    ref_interproscan_map = ipr_map
                else:
                    qry_interproscan_map = ipr_map

                parsers_list.append((parser, interpro_file))

            # Save parse_interproscan outputs to pavprot_out
            for i, (parser, interpro_file) in enumerate(parsers_list):
                file_type = "reference" if i == 0 else "query"
                file_base = Path(interpro_file).stem

                # Save total IPR lengths
                total_ipr_file = os.path.join(pavprot_out, f"{file_base}_total_ipr_length.tsv")
                domain_dist_file = os.path.join(pavprot_out, f"{file_base}_domain_distribution.tsv")

                ipr_map = ref_interproscan_map if i == 0 else qry_interproscan_map
                total_df = pd.DataFrame(list(ipr_map.items()),
                                       columns=['protein_accession', 'total_iprdom_len'])
                total_df.to_csv(total_ipr_file, sep='\t', index=False)

                # Save domain distribution
                domain_stats = parser.domain_distribution()
                if len(domain_stats) > 0:
                    domain_stats.to_csv(domain_dist_file, sep='\t', index=False, na_rep='')
                print(f"  → Saved {file_type} outputs to pavprot_out/", file=sys.stderr)

            print(f"\nNote: Gene IDs not added to output (no GFF provided)", file=sys.stderr)

        # Case 2: Single GFF + Single InterProScan file
        # Auto-detect whether InterProScan matches reference or query transcripts
        elif num_gffs == 1 and len(interproscan_files) == 1:
            print(f"\n[1/4] Single GFF mode: Auto-detecting InterProScan type", file=sys.stderr)
            print(f"  GFF: {ref_gff_list[0]}", file=sys.stderr)
            print(f"  InterProScan: {interproscan_files[0]}", file=sys.stderr)

            print(f"\n[2/4] Auto-detecting InterProScan type...", file=sys.stderr)
            interproscan_type = PAVprot.detect_interproscan_type(data, interproscan_files[0])

            print(f"\n[3/4] Parsing InterProScan with gene mapping...", file=sys.stderr)
            parser = InterProParser(gff_file=ref_gff_list[0])
            df = parser.parse_tsv(interproscan_files[0])
            print(f"  → Loaded {len(df)} InterProScan entries", file=sys.stderr)

            print(f"\n[4/4] Calculating total IPR domain lengths per gene...", file=sys.stderr)
            ipr_map = parser.total_ipr_length()

            if interproscan_type == 'query':
                qry_interproscan_map = ipr_map
                print(f"  → Calculated for {len(qry_interproscan_map)} query genes", file=sys.stderr)
                print(f"  → Reference genes: No InterProScan data", file=sys.stderr)
            else:  # reference or unknown (default to reference)
                ref_interproscan_map = ipr_map
                print(f"  → Calculated for {len(ref_interproscan_map)} reference genes", file=sys.stderr)
                print(f"  → Query genes: No InterProScan data", file=sys.stderr)

            # Save parse_interproscan outputs to pavprot_out
            file_base = Path(interproscan_files[0]).stem
            total_ipr_file = os.path.join(pavprot_out, f"{file_base}_total_ipr_length.tsv")
            domain_dist_file = os.path.join(pavprot_out, f"{file_base}_domain_distribution.tsv")

            # Save total IPR lengths
            total_df = pd.DataFrame(list(ipr_map.items()),
                                    columns=['gene_id' if parser.transcript_to_gene_map else 'protein_accession',
                                            'total_iprdom_len'])
            total_df.to_csv(total_ipr_file, sep='\t', index=False)
            print(f"  → Saved: {total_ipr_file}", file=sys.stderr)

            # Save domain distribution
            domain_stats = parser.domain_distribution()
            if len(domain_stats) > 0:
                domain_stats.to_csv(domain_dist_file, sep='\t', index=False, na_rep='')
                print(f"  → Saved: {domain_dist_file}", file=sys.stderr)

        # Case 2b: Two GFFs + Single InterProScan file
        # Auto-detect whether InterProScan matches reference or query
        elif num_gffs == 2 and len(interproscan_files) == 1:
            print(f"\n[1/4] Dual GFF mode with single InterProScan: Auto-detecting type", file=sys.stderr)
            print(f"  Reference GFF: {ref_gff_list[0]}", file=sys.stderr)
            print(f"  Query GFF: {ref_gff_list[1]}", file=sys.stderr)
            print(f"  InterProScan: {interproscan_files[0]}", file=sys.stderr)

            print(f"\n[2/4] Auto-detecting InterProScan type...", file=sys.stderr)
            interproscan_type = PAVprot.detect_interproscan_type(data, interproscan_files[0])

            # Choose which GFF to use for mapping based on detection
            gff_to_use = ref_gff_list[0] if interproscan_type == 'reference' else ref_gff_list[1]

            print(f"\n[3/4] Parsing InterProScan with gene mapping...", file=sys.stderr)
            parser = InterProParser(gff_file=gff_to_use)
            df = parser.parse_tsv(interproscan_files[0])
            print(f"  → Loaded {len(df)} InterProScan entries", file=sys.stderr)

            print(f"\n[4/4] Calculating total IPR domain lengths per gene...", file=sys.stderr)
            ipr_map = parser.total_ipr_length()

            if interproscan_type == 'query':
                qry_interproscan_map = ipr_map
                print(f"  → Calculated for {len(qry_interproscan_map)} query genes", file=sys.stderr)
                print(f"  → Reference genes: No InterProScan data", file=sys.stderr)
            else:  # reference or unknown
                ref_interproscan_map = ipr_map
                print(f"  → Calculated for {len(ref_interproscan_map)} reference genes", file=sys.stderr)
                print(f"  → Query genes: No InterProScan data", file=sys.stderr)

            # Save parse_interproscan outputs to pavprot_out
            file_base = Path(interproscan_files[0]).stem
            total_ipr_file = os.path.join(pavprot_out, f"{file_base}_total_ipr_length.tsv")
            domain_dist_file = os.path.join(pavprot_out, f"{file_base}_domain_distribution.tsv")

            # Save total IPR lengths
            total_df = pd.DataFrame(list(ipr_map.items()),
                                    columns=['gene_id' if parser.transcript_to_gene_map else 'protein_accession',
                                            'total_iprdom_len'])
            total_df.to_csv(total_ipr_file, sep='\t', index=False)
            print(f"  → Saved: {total_ipr_file}", file=sys.stderr)

            # Save domain distribution
            domain_stats = parser.domain_distribution()
            if len(domain_stats) > 0:
                domain_stats.to_csv(domain_dist_file, sep='\t', index=False, na_rep='')
                print(f"  → Saved: {domain_dist_file}", file=sys.stderr)

        # Case 3: Single GFF + Two InterProScan files
        # Map first InterProScan to GFF (reference), second without mapping (query)
        elif num_gffs == 1 and len(interproscan_files) == 2:
            print(f"\n[1/4] Single GFF mode: Reference with gene mapping, Query without", file=sys.stderr)
            print(f"  Reference GFF: {ref_gff_list[0]}", file=sys.stderr)
            print(f"  Reference InterProScan: {interproscan_files[0]}", file=sys.stderr)
            print(f"  Query InterProScan: {interproscan_files[1]} (no gene mapping)", file=sys.stderr)

            # Load reference InterProScan with GFF mapping
            print(f"\n[2/4] Parsing reference InterProScan with gene mapping...", file=sys.stderr)
            ref_parser = InterProParser(gff_file=ref_gff_list[0])
            ref_df = ref_parser.parse_tsv(interproscan_files[0])
            print(f"  → Loaded {len(ref_df)} InterProScan entries", file=sys.stderr)
            print(f"  → Calculating total IPR lengths per gene...", file=sys.stderr)
            ref_interproscan_map = ref_parser.total_ipr_length()
            print(f"  → Calculated for {len(ref_interproscan_map)} reference genes", file=sys.stderr)

            # Load query InterProScan without GFF mapping
            print(f"\n[3/4] Parsing query InterProScan (protein-level only)...", file=sys.stderr)
            qry_parser = InterProParser(gff_file=None)
            qry_df = qry_parser.parse_tsv(interproscan_files[1])
            print(f"  → Loaded {len(qry_df)} InterProScan entries", file=sys.stderr)
            print(f"  → Calculating total IPR lengths per protein...", file=sys.stderr)
            qry_interproscan_map = qry_parser.total_ipr_length()
            print(f"  → Calculated for {len(qry_interproscan_map)} query proteins (using protein_accession)", file=sys.stderr)

            # Save parse_interproscan outputs to pavprot_out
            ref_base = Path(interproscan_files[0]).stem
            qry_base = Path(interproscan_files[1]).stem

            # Save reference outputs
            ref_total_ipr_file = os.path.join(pavprot_out, f"{ref_base}_total_ipr_length.tsv")
            ref_domain_dist_file = os.path.join(pavprot_out, f"{ref_base}_domain_distribution.tsv")
            ref_total_df = pd.DataFrame(list(ref_interproscan_map.items()),
                                        columns=['gene_id' if ref_parser.transcript_to_gene_map else 'protein_accession',
                                                'total_iprdom_len'])
            ref_total_df.to_csv(ref_total_ipr_file, sep='\t', index=False)
            ref_domain_stats = ref_parser.domain_distribution()
            if len(ref_domain_stats) > 0:
                ref_domain_stats.to_csv(ref_domain_dist_file, sep='\t', index=False, na_rep='')
            print(f"  → Saved reference outputs to pavprot_out/", file=sys.stderr)

            # Save query outputs
            qry_total_ipr_file = os.path.join(pavprot_out, f"{qry_base}_total_ipr_length.tsv")
            qry_domain_dist_file = os.path.join(pavprot_out, f"{qry_base}_domain_distribution.tsv")
            qry_total_df = pd.DataFrame(list(qry_interproscan_map.items()),
                                        columns=['protein_accession', 'total_iprdom_len'])
            qry_total_df.to_csv(qry_total_ipr_file, sep='\t', index=False)
            qry_domain_stats = qry_parser.domain_distribution()
            if len(qry_domain_stats) > 0:
                qry_domain_stats.to_csv(qry_domain_dist_file, sep='\t', index=False, na_rep='')
            print(f"  → Saved query outputs to pavprot_out/", file=sys.stderr)

        # Case 4: Two GFFs + Two InterProScan files
        # Load both reference and query InterProScan data with gene mapping
        elif num_gffs == 2 and len(interproscan_files) == 2:
            print(f"\n[1/4] Dual GFF mode: Reference + Query", file=sys.stderr)
            print(f"  Reference GFF: {ref_gff_list[0]}", file=sys.stderr)
            print(f"  Reference InterProScan: {interproscan_files[0]}", file=sys.stderr)
            print(f"  Query GFF: {ref_gff_list[1]}", file=sys.stderr)
            print(f"  Query InterProScan: {interproscan_files[1]}", file=sys.stderr)

            # Load reference InterProScan with reference GFF
            print(f"\n[2/4] Parsing reference InterProScan...", file=sys.stderr)
            ref_parser = InterProParser(gff_file=ref_gff_list[0])
            ref_df = ref_parser.parse_tsv(interproscan_files[0])
            print(f"  → Loaded {len(ref_df)} InterProScan entries", file=sys.stderr)
            print(f"  → Calculating total IPR lengths per gene...", file=sys.stderr)
            ref_interproscan_map = ref_parser.total_ipr_length()
            print(f"  → Calculated for {len(ref_interproscan_map)} reference genes", file=sys.stderr)

            # Load query InterProScan with query GFF
            print(f"\n[3/4] Parsing query InterProScan...", file=sys.stderr)
            qry_parser = InterProParser(gff_file=ref_gff_list[1])
            qry_df = qry_parser.parse_tsv(interproscan_files[1])
            print(f"  → Loaded {len(qry_df)} InterProScan entries", file=sys.stderr)
            print(f"  → Calculating total IPR lengths per gene...", file=sys.stderr)
            qry_interproscan_map = qry_parser.total_ipr_length()
            print(f"  → Calculated for {len(qry_interproscan_map)} query genes", file=sys.stderr)

            # Save parse_interproscan outputs to pavprot_out
            ref_base = Path(interproscan_files[0]).stem
            qry_base = Path(interproscan_files[1]).stem

            # Save reference outputs
            ref_total_ipr_file = os.path.join(pavprot_out, f"{ref_base}_total_ipr_length.tsv")
            ref_domain_dist_file = os.path.join(pavprot_out, f"{ref_base}_domain_distribution.tsv")
            ref_total_df = pd.DataFrame(list(ref_interproscan_map.items()),
                                        columns=['gene_id' if ref_parser.transcript_to_gene_map else 'protein_accession',
                                                'total_iprdom_len'])
            ref_total_df.to_csv(ref_total_ipr_file, sep='\t', index=False)
            ref_domain_stats = ref_parser.domain_distribution()
            if len(ref_domain_stats) > 0:
                ref_domain_stats.to_csv(ref_domain_dist_file, sep='\t', index=False, na_rep='')
            print(f"  → Saved reference outputs to pavprot_out/", file=sys.stderr)

            # Save query outputs
            qry_total_ipr_file = os.path.join(pavprot_out, f"{qry_base}_total_ipr_length.tsv")
            qry_domain_dist_file = os.path.join(pavprot_out, f"{qry_base}_domain_distribution.tsv")
            qry_total_df = pd.DataFrame(list(qry_interproscan_map.items()),
                                        columns=['gene_id' if qry_parser.transcript_to_gene_map else 'protein_accession',
                                                'total_iprdom_len'])
            qry_total_df.to_csv(qry_total_ipr_file, sep='\t', index=False)
            qry_domain_stats = qry_parser.domain_distribution()
            if len(qry_domain_stats) > 0:
                qry_domain_stats.to_csv(qry_domain_dist_file, sep='\t', index=False, na_rep='')
            print(f"  → Saved query outputs to pavprot_out/", file=sys.stderr)

        # Enrich data with InterProScan information
        if qry_interproscan_map or ref_interproscan_map:
            has_interproscan = True
            print(f"\n[{4 if num_gffs == 2 else 4}/4] Enriching PAVprot data with InterProScan totals...", file=sys.stderr)
            data = PAVprot.enrich_interproscan_data(data, qry_interproscan_map, ref_interproscan_map)
            print(f"  → Added columns: query_gene_total_iprdom_len, ref_gene_total_iprdom_len", file=sys.stderr)
            print(f"\n" + "="*80, file=sys.stderr)
            print(f"✓ InterProScan integration complete!", file=sys.stderr)
            print(f"  Query genes with IPR data: {len(qry_interproscan_map)}", file=sys.stderr)
            print(f"  Reference genes with IPR data: {len(ref_interproscan_map)}", file=sys.stderr)
            print("="*80 + "\n", file=sys.stderr)

    # Output
    pavprot_out = os.path.join(os.getcwd(), 'pavprot_out')
    os.makedirs(pavprot_out, exist_ok=True)

    # Add InterProScan basename prefix when single InterProScan file is provided
    interproscan_prefix = ""
    if interproscan_files and len(interproscan_files) == 1:
        # Extract short basename (remove extensions like .tsv, .faa, etc.)
        interpro_basename = Path(interproscan_files[0]).stem
        # Further clean: remove common suffixes like .prot, .faa
        interproscan_prefix = interpro_basename.replace('.prot', '').replace('.faa', '')

    # Always include "synonym_mapping_liftover_gffcomp" prefix
    base_prefix = "synonym_mapping_liftover_gffcomp"
    if args.output_prefix and args.output_prefix != "synonym_mapping_liftover_gffcomp":
        full_prefix = f"{base_prefix}_{args.output_prefix}"
    else:
        full_prefix = base_prefix

    # Prepend InterProScan prefix if single file
    if interproscan_prefix:
        full_prefix = f"{interproscan_prefix}_{full_prefix}"

    if args.class_code:
        safe_codes = "_".join(sorted(filter_set))
        suffix = "_diamond_blastp.tsv" if args.run_diamond else ".tsv"
        output_file = os.path.join(pavprot_out, f"{full_prefix}_{safe_codes}{suffix}")
    else:
        suffix = "_diamond_blastp.tsv" if args.run_diamond else ".tsv"
        output_file = os.path.join(pavprot_out, f"{full_prefix}{suffix}")

    header = "ref_gene\tref_transcript\tquery_gene\tquery_transcript\tclass_code\texons\tclass_code_multi\tclass_type\temckmnj\temckmnje"
    if args.run_diamond:
        header += "\tidentical_aa\tmismatched_aa\tindels_aa\taligned_aa"
    if args.liftoff_gff:
        header += "\textra_copy_number"
    if has_interproscan:
        header += "\tquery_total_ipr_domain_length\tref_total_ipr_domain_length"

    with open(output_file, 'w') as f:
        f.write(header + "\n")
        for entries in data.values():
            for e in entries:
                exons = e.get('exons') if e.get('exons') is not None else '-'
                base = f"{e['ref_gene']}\t{e['ref_transcript']}\t{e['query_gene']}\t{e['query_transcript']}\t{e['class_code']}\t{exons}\t{e['class_code_multi']}\t{e['class_type']}\t{e['emckmnj']}\t{e['emckmnje']}"

                diamond_line = ""
                if args.run_diamond:
                    diamond_line = f"\t{e.get('identical_aa', 0)}\t{e.get('mismatched_aa', 0)}\t{e.get('indels_aa', 0)}\t{e.get('aligned_aa', 0)}"

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

                f.write(f"{base}{diamond_line}{extra_copy_line}{interproscan_line}\n")
    print(f"Results saved to {output_file}", file=sys.stderr)


if __name__ == '__main__':
    main()