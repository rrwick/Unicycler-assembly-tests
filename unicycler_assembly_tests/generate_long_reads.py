"""
Runs PBSIM to generate fake long reads at multiple sequence rotations (to ensure
circular assembly).

It also allows the user to create a log-normal-based distribution of read lengths and a beta
distribution of read identities.

Author: Ryan Wick
email: rrwick@gmail.com
"""

import random
import os
import subprocess
import argparse
import sys
import gzip
from unicycler_assembly_tests.misc import load_fasta, load_one_read_from_fastq, get_relative_depths


def main():
    args = get_args()
    print()
    print('Making fake long reads for ' + args.reference)
    print('  read length:   ' + str(args.length))
    print('  read identity: ' +
          '%.1f' % (100.0 * args.id_alpha / (args.id_alpha + args.id_beta)) + '%')
    print('  output:        ' + str(args.long))
    print()
    make_fake_long_reads(args.reference, args.long, args.depth, args)
    print()


def get_args():
    """
    Specifies the command line arguments required by the script.
    """
    parser = argparse.ArgumentParser(description='Fake long read generator for bacterial genomes')

    parser.add_argument('--reference', type=str, required=True,
                        help='The reference genome to shred')
    parser.add_argument('-l', '--long', type=str, required=True,
                        help='Synthetic reads output file')
    parser.add_argument('--depth', type=float, default=50.0,
                        help='Read depth')

    parser.add_argument('--length', type=int, default=10000,
                        help='Read length')
    parser.add_argument('--length_sigma', type=float, default=1.0,
                        help='Sigma for the log-normal distribution used for read lengths')
    parser.add_argument('--length_max', type=float, default=100000,
                        help='Maximum allowed read length')

    parser.add_argument('--id_alpha', type=float, default=12,
                        help='Alpha parameter for the beta distribution used to get read identity')
    parser.add_argument('--id_beta', type=float, default=3,
                        help='Beta parameter for the beta distribution used to get read identity')
    parser.add_argument('--id_max', type=float, default=0.95,
                        help='Maximum allowed identity')

    parser.add_argument('--model_qc', type=str, default='model_qc_clr',
                        help='Model QC file for pbsim')

    # Preset options.
    parser.add_argument('--good_nanopore', action='store_true',
                        help='equivalent to --length 20000 --id_alpha 13 --id_beta 2 --id_max 0.98')
    parser.add_argument('--medium_nanopore', action='store_true',
                        help='equivalent to --length 10000 --id_alpha 12 --id_beta 3 --id_max 0.95')
    parser.add_argument('--bad_nanopore', action='store_true',
                        help='equivalent to --length 5000 --id_alpha 11 --id_beta 4 --id_max 0.9')
    parser.add_argument('--good_pacbio', action='store_true',
                        help='equivalent to --length 20000 --id_alpha 90 --id_beta 10 --id_max 1.0')
    parser.add_argument('--medium_pacbio', action='store_true',
                        help='equivalent to --length 10000 --id_alpha 85 --id_beta 15 --id_max 1.0')
    parser.add_argument('--bad_pacbio', action='store_true',
                        help='equivalent to --length 5000 --id_alpha 75 --id_beta 25 --id_max 1.0')

    args = parser.parse_args()

    preset_count = 0
    if args.good_nanopore:
        preset_count += 1
    if args.medium_nanopore:
        preset_count += 1
    if args.bad_nanopore:
        preset_count += 1
    if args.good_pacbio:
        preset_count += 1
    if args.medium_pacbio:
        preset_count += 1
    if args.bad_pacbio:
        preset_count += 1
    if preset_count > 1:
        sys.exit('Only one preset can be used at a time')

    # Nanopore presets have a wider distribution of read identity.
    if args.good_nanopore:
        args.length, args.id_alpha, args.id_beta, args.id_max = 20000, 13, 2, 0.98
    elif args.medium_nanopore:
        args.length, args.id_alpha, args.id_beta, args.id_max = 10000, 12, 3, 0.95
    elif args.bad_nanopore:
        args.length, args.id_alpha, args.id_beta, args.id_max = 5000, 11, 4, 0.9

    # PacBio presets have a narrow distribution of read identity.
    elif args.good_pacbio:
        args.length, args.id_alpha, args.id_beta, args.id_max = 20000, 90, 10, 1.0
    elif args.medium_pacbio:
        args.length, args.id_alpha, args.id_beta, args.id_max = 10000, 85, 15, 1.0
    elif args.bad_pacbio:
        args.length, args.id_alpha, args.id_beta, args.id_max = 5000, 75, 25, 1.0

    # Look for model_qc file in the same directory as this script.
    if args.model_qc == 'model_qc_clr' and not os.path.isfile(args.model_qc):
        args.model_qc = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model_qc_clr')
    if not os.path.isfile(args.model_qc):
        args.model_qc = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                     'model_qc_clr')
    if not os.path.isfile(args.model_qc):
        sys.exit('Count not find ' + args.model_qc)

    return args


def get_read_length(length_factor, log_normal_sigma, max_length):
    read_length = 0
    while read_length == 0 or read_length > max_length:
        read_length = int(round(length_factor * random.lognormvariate(0.0, log_normal_sigma)))
    return read_length


def get_read_identity(alpha, beta, max_id):
    read_id = 0.0
    while read_id == 0.0 or read_id > max_id:
        read_id = random.betavariate(alpha, beta)
    return read_id


def save_ref_to_fasta(ref_seq, temp_fasta_filename):
    with open(temp_fasta_filename, 'wt') as temp_fasta:
        temp_fasta.write('>ref\n')
        temp_fasta.write(ref_seq)
        temp_fasta.write('\n')


def make_fake_long_reads(reference, read_filename, depth, args):
    references = load_fasta(reference)

    relative_depths = get_relative_depths(reference)

    print('\t'.join(['Reference', 'Length', 'Target depth', 'Final depth']))

    temp_fasta_filename = 'temp_' + str(os.getpid()) + '.fasta'

    # This will hold all simulated long reads. Each read is a list of 4 strings: one for each
    # line of the FASTQ.
    long_reads = []

    read_number = 1  # Used to prevent duplicate read names.
    for i, ref in enumerate(references):

        target_depth = relative_depths[i] * depth

        ref_seq = ref[1]
        save_ref_to_fasta(ref_seq, temp_fasta_filename)
        circular = ref[3]

        current_bases = 0
        current_depth = 0.0

        print('\t'.join([ref[0], str(len(ref_seq)), str(target_depth)]), end='', flush=True)

        while current_depth < target_depth:
            read_length = get_read_length(args.length, args.length_sigma, args.length_max)
            read_id = get_read_identity(args.id_alpha, args.id_beta, args.id_max)

            # Don't let the read length get longer than the actual sequence.
            if read_length > len(ref_seq):
                read_length = len(ref_seq)

            # For circular sequences, we rotate the reference sequence.
            if circular:
                random_start = random.randint(0, len(ref_seq) - 1)
            else:
                random_start = 0
            rotated = ref_seq[random_start:] + ref_seq[:random_start]
            save_ref_to_fasta(rotated, temp_fasta_filename)

            long_reads.append(run_pbsim(temp_fasta_filename, read_length, read_id, args,
                                        len(ref_seq)))
            os.remove(temp_fasta_filename)

            read_number += 1
            current_bases += read_length
            current_depth = current_bases / len(ref_seq)
        print('\t' + str(current_depth), flush=True)

    long_reads = [x for x in long_reads if len(x[0]) > 0]
    random.shuffle(long_reads)

    gzip_after = read_filename.endswith('.gz')
    if gzip_after:
        out_file = read_filename.replace('.gz', '')
    else:
        out_file = read_filename

    with open(out_file, 'wt') as reads:
        for i, read in enumerate(long_reads):
            read_name = '@long_read_' + str(i+1)
            reads.write(read_name)
            reads.write('\n')
            reads.write(read[0])
            reads.write('\n+\n')
            reads.write(read[1])
            reads.write('\n')

    if gzip_after:
        process = subprocess.Popen(['gzip', out_file], stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        _, _ = process.communicate()


def run_pbsim(input_fasta, read_length, read_id, args, ref_len):

    # We only want one read, so adjust the depth to give us that.
    depth = 1.5 * read_length / ref_len

    prefix = str(os.getpid())

    pbsim_command = ['pbsim',
                     '--depth', str(depth),
                     '--length-min', str(read_length),
                     '--length-max', str(read_length),
                     '--length-mean', str(read_length),
                     '--length-sd', '0',
                     '--accuracy-min', str(read_id),
                     '--accuracy-max', str(read_id),
                     '--accuracy-mean', str(read_id),
                     '--accuracy-sd', '0',
                     '--model_qc', args.model_qc,
                     '--difference-ratio', '10:40:30',
                     '--seed', str(random.randint(0, 1000000)),
                     '--prefix', prefix,
                     input_fasta]

    process = subprocess.Popen(pbsim_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _, _ = process.communicate()

    reads = load_one_read_from_fastq(prefix + '_0001.fastq')
    os.remove(prefix + '_0001.fastq')
    os.remove(prefix + '_0001.maf')
    os.remove(prefix + '_0001.ref')

    return reads


if __name__ == '__main__':
    main()
