#!/usr/bin/env python

import sys

def fasta_to_dict(file_path):
    """
    Parses a FASTA file and returns its contents as a dictionary.

    Args:
        file_path (str): The path to the FASTA file.

    Returns:
        dict: A dictionary where keys are sequence headers (without '>')
              and values are the corresponding sequences.
    """
    sequences = {}
    current_header = None
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('>'):
                    current_header = line[1:]
                    sequences[current_header] = ''
                elif current_header:
                    sequences[current_header] += line
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}", file=sys.stderr)
        return None
    return sequences

if __name__ == "__main__":
    # These file paths can be changed or passed as command-line arguments

    q_prot_dict = fasta_to_dict("test.fa")
    print(q_prot_dict)

    # if q_prot_dict and r_prot_dict:
    #     print(f"Successfully loaded {len(q_prot_dict)} sequences from {q_prot_file}")
    #     print(f"Successfully loaded {len(r_prot_dict)} sequences from {r_prot_file}")

    #     # You can now work with these dictionaries. For example, print one sequence.
    #     if q_prot_dict:
    #         first_key = next(iter(q_prot_dict))
    #         print(f"\nExample sequence from {q_prot_file}:")
    #         print(f">{first_key}")
    #         print(q_prot_dict[first_key])
