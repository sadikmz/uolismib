seq_dict = {}
current_header = None
current_seq = []

try:
    with open("test.fa", 'r') as f:
        for line in f:
            # iterate through each line in the FASTA file and remove leading/trailing whitespace
            line = line.strip()
            # skip empty lines
            if not line:
                continue
            # if the line starts with '>', it's a header line 
            if line.startswith('>'):
                # if we were collecting a sequence, save it to the dictionary - save the previous sequence
                if current_header:
                    seq_dict[current_header] = ''.join(current_seq)
                # remove '>' and set the current header
                current_header = line[1:]
                # reset the current sequence
                current_seq = []
            # if it's a sequence line, append it to the current sequence list - must be a sequence line hence part of the current header
            else:
                current_seq.append(line)
        
        #  after the loop, save the last sequence if exists
        if current_header:
            seq_dict[current_header] = ''.join(current_seq)
except FileNotFoundError:
    print("Error: File not found.", file=sys.stderr)
    