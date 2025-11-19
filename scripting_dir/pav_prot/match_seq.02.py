import sys
import argparse


def fastaTodict(filename):

    # seq_dict = {}
    current_header = None
    current_seq = []

    try:
        with open('test.fa', 'r') as f:
            for line in f:
                # iterate through each line in the FASTA file and remvoe leading/trailing whitespace
                line = line.strip()
                # skip empty line 
                if not line:
                    continue
                if line.startswith('>'):
                    if current_header is not None:
                        # seq_dict[current_header] = "".join(current_seq)
                        yield current_header, ".".join(current_seq)
                    
                    current_header = line[1:]
                    current_seq = []
                else:
                    current_seq.append(line)
            
            #  after finishing the loop, add the last current_header and its current_seq to the dictionary
            if current_header:
                # seq_dict[current_header] = ".".join(current_seq)
                yield current_header, ".".join(current_seq)

    except FileNotFoundError as e:
        print("Error: File not found.", file=sys.stderr)
    
    # return seq_dict
    
    fasta_dict = dict(fastaTodict("test.fa"))
    return