#!/usr/bin/env python3

import argparse
import sys

class PAVprot:
    
    # Static method to convert FASTA to dict 
    def fasta2dict(source):
        """
        Generator: yields (header, sequence) from FASTA file or stdin.
        Uses 'with open' automatically when given a file path.
        """
        # If user passed '-', read from stdin
        if str(source) == '-':
            lines = sys.stdin
            close_at_end = False
        else:
            lines = open(source, 'r')
            close_at_end = True  # not needed with 'with', but kept for clarity

        # Use context manager only if we opened the file
        context = lines if not close_at_end else open(source, 'r')

        with context:
            current_header = None
            current_seq = []

            for line in context:
                line = line.strip()
                if not line:
                    continue

                if line.startswith('>'):
                    if current_header:
                        yield current_header, ''.join(current_seq)

                    header_line = line[1:].strip()
                    current_header = header_line
                    current_seq = []
                else:
                    current_seq.append(line)

            # Yield the last sequence
            if current_header:
                yield current_header, ''.join(current_seq)


def main():
    parser = argparse.ArgumentParser(
        description="FASTA → Python dict  {header: sequence}  – pure Python, safe & fast"
    )
    parser.add_argument('fasta_file', nargs='?', default='-', 
                        help="FASTA file or '-' to read from stdin (default: stdin)")
    parser.add_argument('--quiet', action='store_true',
                        help="Validate only – no output")

    args = parser.parse_args()

    try:
        seq_dict = dict(PAVprot.fasta2dict(args.fasta_file))
        if not args.quiet:
            print(seq_dict)

    except Exception as e:
        print(f"Error reading FASTA: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
    
    
    
# test = dict(fasta2dict("../test.fa"))
# print(test)