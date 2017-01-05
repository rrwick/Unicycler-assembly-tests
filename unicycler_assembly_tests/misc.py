"""
Author: Ryan Wick
email: rrwick@gmail.com
"""

import sys
import gzip


def load_fasta(filename):
    """
    Returns a list of tuples (header, seq, depth, circular) for each record in the fasta file.
    """
    if get_compression_type(filename) == 'gz':
        open_func = gzip.open
    else:  # plain text
        open_func = open

    fasta_seqs = []
    with open_func(filename, 'rt') as fasta_file:
        name = ''
        sequence = ''
        for line in fasta_file:
            line = line.strip()
            if not line:
                continue
            if line[0] == '>':  # Header line = start of new contig
                if name:
                    seq_name = name.split()[0]
                    try:
                        relative_depth = float(name.split('depth=')[1].split()[0])
                    except IndexError:
                        relative_depth = 1.0
                    circular = 'circular=true' in name.lower()
                    fasta_seqs.append((seq_name, sequence, relative_depth, circular))
                    sequence = ''
                name = line[1:]
            else:
                sequence += line
        if name:
            seq_name = name.split()[0]
            try:
                relative_depth = float(name.split('depth=')[1].split()[0])
            except IndexError:
                relative_depth = 1.0
            circular = 'circular=true' in name.lower()
            fasta_seqs.append((seq_name, sequence, relative_depth, circular))
    return fasta_seqs


def load_one_read_from_fastq(fastq_filename):
    if get_compression_type(fastq_filename) == 'gz':
        open_func = gzip.open
    else:  # plain text
        open_func = open
    with open_func(fastq_filename, 'rt') as fastq:
        for _ in fastq:
            sequence = next(fastq).strip()
            _ = next(fastq)
            qualities = next(fastq).strip()
            return sequence, qualities
    return '', ''


def get_compression_type(filename):
    """
    Attempts to guess the compression (if any) on a file using the first few bytes.
    http://stackoverflow.com/questions/13044562
    """
    magic_dict = {'gz': (b'\x1f', b'\x8b', b'\x08'),
                  'bz2': (b'\x42', b'\x5a', b'\x68'),
                  'zip': (b'\x50', b'\x4b', b'\x03', b'\x04')}
    max_len = max(len(x) for x in magic_dict)

    unknown_file = open(filename, 'rb')
    file_start = unknown_file.read(max_len)
    unknown_file.close()
    compression_type = 'plain'
    for filetype, magic_bytes in magic_dict.items():
        if file_start.startswith(magic_bytes):
            compression_type = filetype
    if compression_type == 'bz2':
        sys.exit('cannot use bzip2 format - use gzip instead')
    if compression_type == 'zip':
        sys.exit('cannot use zip format - use gzip instead')
    return compression_type


def get_relative_depths(reference):
    references = load_fasta(reference)
    longest_len = 0
    longest_depth = 0.0
    relative_depths = []
    for ref in references:
        try:
            depth = float(ref[2])
        except ValueError:
            depth = 1.0
        relative_depths.append(depth)
        length = len(ref[1])
        if length > longest_len:
            longest_len = length
            longest_depth = depth
    return [x / longest_depth for x in relative_depths]
