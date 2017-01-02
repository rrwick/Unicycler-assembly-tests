"""
Runs ART to generate fake Illumina reads at multiple sequence rotations (to ensure
circular assembly).

Author: Ryan Wick
email: rrwick@gmail.com
"""

import random
import os
import subprocess
import argparse
import sys
import gzip
from unicycler_assembly_tests.misc import load_fasta, get_relative_depths


def main():
    args = get_args()
    make_fake_short_reads(args.reference, args.short_1, args.short_2, args.depth,
                          args.rotation_count, args.platform)


def get_args():
    """
    Specifies the command line arguments required by the script.
    """
    parser = argparse.ArgumentParser(description='Fake Illumina read generator for bacterial '
                                                 'genomes')

    # Platform options mimic those available in ART.
    platform_options = ['GA1_36', 'GA1_44', 'GA2_50', 'GA2_75', 'HS10_100', 'HS20_100', 'HS25_125',
                        'HS25_150', 'HSXn_150', 'HSXt_150', 'MinS_50', 'MSv1_250', 'MSv3_250',
                        'NS50_75']

    parser.add_argument('--reference', type=str, required=True,
                        help='The reference genome to shred')
    parser.add_argument('-1', '--short_1', type=str, required=True,
                        help='Synthetic reads output file (first reads of pair)')
    parser.add_argument('-2', '--short_2', type=str, required=True,
                        help='Synthetic reads output file (second reads of pair)')
    parser.add_argument('--rotation_count', type=int, default=50,
                        help='The number of times to run ART with random start positions')
    parser.add_argument('--depth', type=float, default=50.0,
                        help='Read depth')
    parser.add_argument('--platform', type=str, default='HS25_125',
                        help='Illumina platform and read length (same as ART options: GA1_36, '
                             'GA1_44, GA2_50, GA2_75, HS10_100, HS20_100, HS25_125, HS25_150, '
                             'HSXn_150, HSXt_150, MinS_50, MSv1_250, MSv3_250, NS50_75)')

    # Preset options.
    parser.add_argument('--good', action='store_true',
                        help='equivalent to --depth 80.0 --platform MSv3_250')
    parser.add_argument('--medium', action='store_true',
                        help='equivalent to --depth 45.0 --platform HS25_125')
    parser.add_argument('--bad', action='store_true',
                        help='equivalent to --depth 40.0 --platform HS10_100')

    args = parser.parse_args()

    preset_count = 0
    if args.good:
        preset_count += 1
    if args.medium:
        preset_count += 1
    if args.bad:
        preset_count += 1
    if preset_count > 1:
        sys.exit('Only one preset can be used at a time')

    if args.good:
        args.depth, args.platform = 80.0, 'MSv3_250'
    elif args.medium:
        args.depth, args.platform = 45.0, 'HS25_125'
    elif args.bad:
        args.depth, args.platform = 40.0, 'HS10_100'

    if args.platform not in platform_options:
        sys.exit('--platform must be one of the following: ' + ', '.join(platform_options))

    return args


def make_fake_short_reads(reference, read_filename_1, read_filename_2, depth, rotation_count,
                          platform):
    references = load_fasta(reference)
    relative_depths = get_relative_depths(reference)

    # This will hold all simulated short reads. Each read is a list of 8 strings: the first four are
    # for the first read in the pair, the second four are for the second.
    short_read_pairs = []

    read_prefix = 1  # Used to prevent duplicate read names.
    for i, ref in enumerate(references):

        short_depth = relative_depths[i] * depth

        ref_seq = ref[1]
        circular = ref[3]

        if circular:
            short_depth_per_rotation = short_depth / rotation_count

            for j in range(rotation_count):

                # Randomly rotate the sequence.
                random_start = random.randint(0, len(ref_seq) - 1)
                rotated = ref_seq[random_start:] + ref_seq[:random_start]

                # Save the rotated sequence to FASTA.
                temp_fasta_filename = 'temp_rotated.fasta'
                temp_fasta = open(temp_fasta_filename, 'w')
                temp_fasta.write('>' + ref[0] + '\n')
                temp_fasta.write(rotated + '\n')
                temp_fasta.close()

                short_read_pairs += run_art(temp_fasta_filename, short_depth_per_rotation,
                                            str(read_prefix), platform)
                os.remove(temp_fasta_filename)
                read_prefix += 1

        else:  # linear
            temp_fasta_filename = 'temp.fasta'
            temp_fasta = open(temp_fasta_filename, 'w')
            temp_fasta.write('>' + ref[0] + '\n')
            temp_fasta.write(ref_seq + '\n')
            temp_fasta.close()

            short_read_pairs += run_art(temp_fasta_filename, short_depth, str(read_prefix),
                                        platform)
            os.remove(temp_fasta_filename)
            read_prefix += 1

    random.shuffle(short_read_pairs)
    with gzip.open(read_filename_1, 'wt') as reads_1, gzip.open(read_filename_2, 'wt') as reads_2:
        for i, read_pair in enumerate(short_read_pairs):
            read_name = '@short_read_' + str(i+1)
            reads_1.write(read_name + '/1')
            reads_1.write('\n')
            reads_1.write(read_pair[1])
            reads_1.write('\n')
            reads_1.write(read_pair[2])
            reads_1.write('\n')
            reads_1.write(read_pair[3])
            reads_1.write('\n')
            reads_2.write(read_name + '/2')
            reads_2.write('\n')
            reads_2.write(read_pair[5])
            reads_2.write('\n')
            reads_2.write(read_pair[6])
            reads_2.write('\n')
            reads_2.write(read_pair[7])
            reads_2.write('\n')


def run_art(input_fasta, depth, read_prefix, platform):
    """
    Runs ART and returns reads as list of list of strings.
    """
    seq_sys = platform.split('_')[0]
    read_length = platform.split('_')[1]
    insert_size = min(500, int(read_length) * 3.5)
    insert_stdev = max(50, insert_size // 8)

    art_command = ['art_illumina',
                   '--seqSys', seq_sys,
                   '--in', input_fasta,
                   '--len', read_length,
                   '--mflen', str(insert_size),
                   '--sdev', str(insert_stdev),
                   '--fcov', str(depth),
                   '--out', 'art_output']
    try:
        subprocess.check_output(art_command, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        sys.exit('ART encountered an error:\n' + e.output.decode())

    output_fastq_1_filename = 'art_output1.fq'
    output_fastq_2_filename = 'art_output2.fq'
    try:
        with open(output_fastq_1_filename, 'rt') as f:
            fastq_1_lines = f.read().splitlines()
        with open(output_fastq_2_filename, 'rt') as f:
            fastq_2_lines = f.read().splitlines()
        pair_count = int(len(fastq_1_lines) / 4)
    except FileNotFoundError:
        sys.exit('Could not find ART output read files')

    os.remove('art_output1.fq')
    os.remove('art_output2.fq')
    os.remove('art_output1.aln')
    os.remove('art_output2.aln')

    read_pairs = []
    i = 0
    for _ in range(pair_count):
        name_1 = '@' + read_prefix + '_' + fastq_1_lines[i].split('-')[1]
        name_2 = '@' + read_prefix + '_' + fastq_2_lines[i].split('-')[1]
        seq_1 = fastq_1_lines[i + 1]
        seq_2 = fastq_2_lines[i + 1]
        qual_1 = fastq_1_lines[i + 3]
        qual_2 = fastq_2_lines[i + 3]

        read_pairs.append((name_1, seq_1, '+', qual_1, name_2, seq_2, '+', qual_2))
        i += 4

    return read_pairs


if __name__ == '__main__':
    main()
