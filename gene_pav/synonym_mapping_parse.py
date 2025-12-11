#!/usr/bin/env python3

from curses import start_color
import pandas as pd

NAMES = [
"GCF_013085055.1_gene",
"GCF_013085055.1_transcript",
"FungiDB-68_Fo47_gene",	
"FungiDB-68_Fo47_Fo47_transcript",	
"gffcompare_class_code",
"exons",	
"class_code_multi",
"class_type",
"emckmnj",	
"emckmnje"
]

def main(args):
    df = pd.read_csv(args.input_tsv, sep='\t', header=None )
    df.columns = NAMES
    
    # print(df)
    
    # find the longest hit with an IntroPro ID
    # df["length"] = df["stop_location"] - df["start_location"] + 1
    df_grouped = df.groupby["GCF_013085055.1_gene"]
    df_sorted = df.sort_values(by=["length"], ascending=False)
    df_sorted.drop_duplicates(subset=["protein_accession"], keep="first", inplace=True)
    
    df_sorted["chosen_name"] = df_sorted.apply(
        lambda row:row["interpro_accession"] 
        if row["interpro_accession"].startswith("IPR")
        else row["signature_accession"],
        axis=1
    )
    print(df_sorted)
    
    

def parse_args():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="")
    
    parser.add_argument(
        "--input_tsv",
        required=True,
        help="Input TSV file with InterPro IDs in the second column"
    )
    return parser.parse_args()
    
if __name__ == "__main__":
    args = parse_args()
    main(args)
    

   import sys
     import pandas as pd

     def count_unique_qry_genes_pandas(input_file):
         """Count unique query genes for each reference gene using pandas"""

         # Read the TSV file
         df = pd.read_csv(input_file, sep='\t')

         # Count unique query genes per reference gene
         result = df.groupby('ref_gene')['query_gene'].nunique().reset_index()
         result.columns = ['ref_gene', 'unique_qry_gene_count']

         # Sort by ref_gene
         result = result.sort_values('ref_gene')

         # Print results
         print(result.to_csv(sep='\t', index=False))

         # Print summary statistics
         print(f"\n# Total reference genes: {len(result)}", file=sys.stderr)
         print(f"# Min unique query genes: {result['unique_qry_gene_count'].min()}", file=sys.stderr)
         print(f"# Max unique query genes: {result['unique_qry_gene_count'].max()}", file=sys.stderr)
         print(f"# Average unique query genes: {result['unique_qry_gene_count'].mean():.2f}", file=sys.stderr)

         # Show distribution
         print(f"\n# Distribution of unique query gene counts:", file=sys.stderr)
         print(result['unique_qry_gene_count'].value_counts().sort_index().to_string(), file=sys.stderr)

     if __name__ == '__main__':
         if len(sys.argv) != 2:
             print("Usage: python3 count_unique_qry_genes_pandas.py <pavprot_output.tsv>", file=sys.stderr)
             sys.exit(1)

         count_unique_qry_genes_pandas(sys.argv[1])