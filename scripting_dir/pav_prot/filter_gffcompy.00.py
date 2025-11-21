# #!/usr/bin/env python3
# """
# Parse StringTie/gffcompare .tracking file and build a dictionary
# showing the relationship between reference transcripts and query transcripts.
# Key features:
# - Handles all class codes (= → 'em', j, m, n, u, etc.)
# - Includes novel transcripts ('u') with ref_gene/ref_transcript = 'NA'
# - Optional filtering by one or more class codes via --class-code
# - Accepts only file path
# """

from collections import defaultdict
from typing import Dict, List
import argparse
import json
import sys

# def parse_gffcompare_tracking(
#     filepath: str,
#     filter_codes: set = None
# ) -> Dict[str, List[dict]]:
#     """
#     Parse a gffcompare .tracking file.

#     Parameters
#     ----------
#     filepath : str
#         Path to the .tracking file
#     filter_codes : set or None
#         If provided, only keep transcripts that have at least one entry matching any code in the set
#         Example: {"em", "j"} → keep only exact matches and contained-in-reference

#     Returns
#     -------
#     dict
#         transcript_id → list of relationship dicts (filtered if requested)
#     """
#     result = defaultdict(list)
#     filter_codes = filter_codes or set()   # empty set = keep everything

#     with open(filepath) as f:
#         for line in f:
#             line = line.rstrip('\n')
#             if not line or line.startswith('#'):
#                 continue

#             fields = line.split('\t')
#             if len(fields) < 5:
#                 continue

#             ref_field  = fields[2].strip()
#             class_code = fields[3].strip()
#             if class_code == '=':
#                 class_code = 'em'

#             query_info = fields[4].strip()
#             parts = query_info.split('|')
#             if len(parts) < 3:
#                 continue

#             ref_gene_full  = parts[0]
#             ref_gene       = ref_gene_full.split(':')[-1]
#             ref_transcript = parts[1]
#             try:
#                 exons = int(parts[2])
#             except ValueError:
#                 exons = None

#             # Determine key and refs
#             if ref_field == '-' or '|' not in ref_field:
#                 transcript_key = ref_transcript
#                 ref_gene = ref_transcript = 'NA'
#             else:
#                 transcript_key = ref_field.split('|')[-1]

#             entry = {
#                 "ref_gene": ref_gene,
#                 "ref_transcript": ref_transcript,
#                 "class_code": class_code,
#                 "exons": exons
#             }
#             result[transcript_key].append(entry)

#     # Apply filtering if requested
#     if filter_codes:
#         filtered = {}
#         for tid, entries in result.items():
#             if any(e["class_code"] in filter_codes for e in entries):
#                 filtered[tid] = entries
#         return filtered
#     # else:
#     #     return dict(result)


# # ———————— Command-line interface ————————
# if __name__ == '__main__':
#     parser = argparse.ArgumentParser(
#         description="Parse gffcompare .tracking file → dict of transcript relationships"
#     )
#     parser.add_argument('tracking_file', help="Path to the .tracking file")
#     parser.add_argument(
#         '--class-code',
#         type=str,
#         default=None,
#         # choices=['em', 'j', 'm', 'n', 'u', 'o', 'x', 'e', 'p', 'k', 's', 'i', 'y', 'c'],
#         help="Comma-separated class codes to filter (eg. 'em,j,u'). Use em for exact match (=)."
#     )
#     parser.add_argument('--pretty', action='store_true', help="Pretty-print JSON output")

#     args = parser.parse_args()

#     filter_set = None
#     if args.class_code:
#         # codes = {c.strip() for c in args.class_code.split(',') if c.strip()}
#         # codes = {code.strip() for code in args.class_code.split(',') if code.strip()}
#         filter_set = {code.strip() for code in args.class_code.split(',') if code.strip()}
#         # filter_set = codes
        
#     # set(args.class_code) if args.class_code else None

#     relationships = parse_gffcompare_tracking(args.tracking_file, filter_set)

#     if args.pretty:
#         print(json.dumps(relationships, indent=2))
#     else:
#         print(json.dumps(relationships))

# def parse_gffcompare_tracking_by_gene(filepath: str, filter_codes: set = None) -> dict:
#     """
#     New structure: grouped by reference gene (prot1)
#     {
#         "gene-FOBCDRAFT_430": [
#             {"gene-FOBCDRAFT_430": "XM_031180643.3", "FOZG_02018": "FOZG_02018-t36_1", "class_code": "j",  "exons": 6},
#             {"gene-FOBCDRAFT_430": "XM_031180643.3", "FOZG_02018": "FOZG_02018-t36_2", "class_code": "n",  "exons": 5},
#             ...
#         ],
#         ...
#     }
#     """
#     result = defaultdict(list)
#     filter_codes = filter_codes or set()

#     with open(filepath) as f:
#         for line in f:
#             line = line.rstrip('\n')
#             if not line or line.startswith('#'):
#                 continue

#             fields = line.split('\t')
#             if len(fields) < 5:
#                 continue

#             ref_field = fields[2].strip()          # gene-FOBCDRAFT_430|rna-XM_031180643.3  or "-"
#             if ref_field == '-' or '|' not in ref_field:
#                 continue  # skip novel transcripts for this structure

#             class_code = fields[3].strip()
#             if class_code == '=':
#                 class_code = 'em'

#             query_info = fields[4].strip()
#             parts = query_info.split('|')
#             if len(parts) < 3:
#                 continue

#             # prot1 side (reference)
#             ref_gene_id, ref_transcript_id = [x.strip() for x in ref_field.split('|')]
#             # remove 'rna-' prefix if present
#             ref_transcript_clean = ref_transcript_id.replace('rna-', '')

#             # prot2 side (query)
#             q_gene_full = parts[0]
#             q_gene_id = q_gene_full.split(':')[-1] if ':' in q_gene_full else q_gene_full
#             q_transcript_id = parts[1]
#             try:
#                 exons = int(parts[2])
#             except ValueError:
#                 exons = None

#             entry = {
#                 ref_gene_id: ref_transcript_clean,
#                 q_gene_id: q_transcript_id,
#                 "class_code": class_code,
#                 "exons": exons
#             }

#             # Optional filtering
#             if not filter_codes or class_code in filter_codes:
#                 result[ref_gene_id].append(entry)

#     return dict(result)
#!/usr/bin/env python3
# import json
# from collections import defaultdict
# import argparse

# def parse_gffcompare_tracking_by_gene(tracking_content: str, filter_codes: set = None):
#     """
#     Input: raw .tracking text (string)
#     Optional filter_codes: e.g. {"em", "j"}
#     Output: dict grouped by reference gene (prot1)
#     """
#     result = defaultdict(list)
#     filter_codes = filter_codes or set()

#     for line in tracking_content.strip().split('\n'):
#         line = line.rstrip('\n')
#         if not line or line.startswith('#'):
#             continue

#         fields = line.split('\t')
#         if len(fields) < 5:
#             continue

#         ref_field = fields[2].strip()
#         if ref_field == '-' or '|' not in ref_field:
#             continue  # skip novel

#         class_code = fields[3].strip()
#         if class_code == '=':
#             class_code = 'em'

#         # Apply filtering early if requested
#         if filter_codes and class_code not in filter_codes:
#             continue

#         query_info = fields[4].strip()
#         parts = query_info.split('|')
#         if len(parts) < 3:
#             continue

#         # prot1 (reference)
#         ref_gene, ref_trans = [x.strip() for x in ref_field.split('|')]
#         ref_trans_clean = ref_trans.replace('rna-', '')

#         # prot2 (query)
#         q_gene_full = parts[0]
#         q_gene = q_gene_full.split(':')[-1]
#         q_trans = parts[1]
#         try:
#             exons = int(parts[2])
#         except ValueError:
#             exons = None

#         entry = {
#             ref_gene: ref_trans_clean,
#             q_gene: q_trans,
#             "class_code": class_code,
#             "exons": exons
#         }
#         result[ref_gene].append(entry)

#     return dict(result)


# # ———————— Command-line + filtering (no file needed) ————————
# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Parse gffcompare .tracking (in-memory) with optional class_code filtering")
#     parser.add_argument('tracking_content', nargs='?', default=None, help="Path to .tracking file OR paste content directly")
#     parser.add_argument('--class-code', type=str, help="Comma-separated class codes, e.g. em,j,u")
#     parser.add_argument('--pretty', action='store_true', help="Pretty JSON output")

#     args = parser.parse_args()

#     # Load content
#     if args.tracking_content and args.tracking_content.endswith('.tracking'):
#         with open(args.tracking_content) as f:
#             content = f.read()
#     else:
#         # Default test data if nothing provided
#         content = """
# TCONS_00000058|4|1243	XLOC_000055	gene-FOBCDRAFT_266382|rna-XM_031180388.3	j	q1:FOZG_02279|FOZG_02279-t36_1|4|0.000000|0.000000|0.000000|1243
# TCONS_00000059|3|1299	XLOC_000055	gene-FOBCDRAFT_266382|rna-XM_031180388.3	m	q1:FOZG_02279|FOZG_02279-t36_2|3|0.000000|0.000000|0.000000|1299
# TCONS_00000215|6|2902	XLOC_000185	gene-FOBCDRAFT_430|rna-XM_031180643.3	j	q1:FOZG_02018|FOZG_02018-t36_1|6|0.000000|0.000000|0.000000|2902
# TCONS_00000217|5|3081	XLOC_000185	gene-FOBCDRAFT_430|rna-XM_031180643.3	=	q1:FOZG_02018|FOZG_02018-t36_3|5|0.000000|0.000000|0.000000|3081
# TCONS_00001849|3|846	XLOC_001148	gene-FOBCDRAFT_209856|rna-XM_059609290.1	=	q1:FOZG_17471|FOZG_17471-t36_1|3|0.000000|0.000000|0.000000|846
#         """

#     filter_set = {c.strip() for c in args.class_code.split(',')} if args.class_code else None

#     relationships = parse_gffcompare_tracking_by_gene(content, filter_set)

#     print(json.dumps(relationships, indent=2 if args.pretty else None))

#!/usr/bin/env python3
"""
Parse gffcompare .tracking → TSV table of matches (filtered or all)
Grouped by reference gene (prot1)
"""

from collections import defaultdict
import argparse
import sys

def parse_gffcompare_tracking(filepath: str, filter_codes: set = None):
    full_dict = defaultdict(list)      # original unfiltered
    filtered_dict = defaultdict(list)  # only matching class codes

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

            # prot1 (reference)
            ref_gene, ref_trans = [x.strip() for x in ref_field.split('|')]
            ref_trans_clean = ref_trans.replace('rna-', '')

            # prot2 (query)
            q_gene_full = parts[0]
            q_gene = q_gene_full.split(':')[-1]
            q_trans = parts[1]
            try:
                exons = int(parts[2])
            except ValueError:
                exons = None

            entry = {
                "ref_gene": ref_gene,
                "ref_transcript": ref_trans_clean,
                "query_gene": q_gene,
                "query_transcript": q_trans,
                "class_code": class_code,
                "exons": exons
            }

            # Always add to full dict
            full_dict[ref_gene].append(entry)

            # Add to filtered only if no filter or matches
            if not filter_codes or class_code in filter_codes:
                filtered_dict[ref_gene].append(entry)

    return dict(full_dict), dict(filtered_dict)


# ———————— TSV output only ————————
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Parse gffcompare .tracking → TSV table (grouped by reference gene)"
    )
    parser.add_argument('tracking_file', help="Path to the .tracking file")
    parser.add_argument(
        '--class-code',
        type=str,
        help="Comma-separated class codes to filter (e.g. em,j). Use 'em' for exact match"
    )
    parser.add_argument(
        '--tsv',
        action='store_true',
        help="Output as TSV (default behavior now)"
    )

    args = parser.parse_args()

    filter_set = None
    if args.class_code:
        filter_set = {c.strip() for c in args.class_code.split(',') if c.strip()}

    full_rels, filtered_rels = parse_gffcompare_tracking(args.tracking_file, filter_set)

    # Use filtered if exists, otherwise full
    data_to_print = filtered_rels if filtered_rels else full_rels

    # Print TSV header
    print("ref_gene\tref_transcript\tquery_gene\tquery_transcript\tclass_code\texons")

    # Print rows
    for ref_gene, entries in data_to_print.items():
        for e in entries:
            print(f"{e['ref_gene']}\t{e['ref_transcript']}\t{e['query_gene']}\t{e['query_transcript']}\t{e['class_code']}\t{e['exons'] or '-'}")