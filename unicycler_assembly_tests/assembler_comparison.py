"""
This is a tool for assembling read sets (short-only or hybrid) using different assemblers.

It can be run on real reads (using --real_read_dir) in which case it groups up read sets by
filename. Alternatively, it can be run on the fake reads generated by the other scripts in this
repository (using --fake_read_dir) in which case it makes all possible combinations of short and
long read files.

Author: Ryan Wick
email: rrwick@gmail.com
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
import copy
import fcntl
from collections import OrderedDict
import unicycler.assembly_graph
from unicycler_assembly_tests.misc import load_fasta


def main():
    args = get_arguments()

    read_sets = []
    if args.real_read_dir:
        read_sets += group_real_reads(args.real_read_dir)
    if args.fake_read_dir:
        read_sets += group_fake_reads(args.fake_read_dir)

    commands = Commands(args.command_file)
    assembly_dir = os.path.join(args.out_dir, 'ASSEMBLY_TEMP_' + str(os.getpid()))
    create_results_table(args.out_dir)

    # Remove read sets this assembler can't handle. E.g. if it's a hybrid read set and a short
    # read only assembler.
    can_do_short_only = bool(commands.short_read_assembly_commands)
    can_do_hybrid = bool(commands.hybrid_assembly_commands)
    filtered_read_sets = []
    for read_set in read_sets:
        if read_set.get_set_type() == 'short-only' and can_do_short_only:
            filtered_read_sets.append(read_set)
        elif read_set.get_set_type() == 'hybrid' and can_do_hybrid:
            filtered_read_sets.append(read_set)
    read_sets = filtered_read_sets

    if args.ref_dir:
        for read_set in read_sets:
            read_set.find_reference(args.ref_dir)

    print('\n')
    print(bold_yellow_underline('Read sets to assemble'))
    if not read_sets:
        print('None')
    for read_set in read_sets:
        print(str(read_set))
    print('\nAssembly temp directory: ' + assembly_dir + '\n', flush=True)

    for read_set in read_sets:
        print()
        print(bold_yellow_underline('Read set: ' + read_set.set_name))

        # Don't bother if the file already exists. This lets us resume crashed/stopped runs
        # without repeating too much work.
        _, copied_fasta = get_copied_fasta_name(read_set, commands, args.out_dir)
        if os.path.isfile(copied_fasta):
            print('Already done')
            continue

        os.makedirs(assembly_dir)
        assembly_time, assembly_stdout = execute_commands(commands, read_set, assembly_dir)
        evaluate_results(commands, read_set, assembly_dir, assembly_time, assembly_stdout,
                         args.out_dir)
        shutil.rmtree(assembly_dir)


def get_arguments():
    parser = argparse.ArgumentParser(description='Assembler comparison tool')
    parser.add_argument('--real_read_dir', type=str,
                        help='Directory containing read sets (named as *_1.fastq.gz, *_2.fastq.gz '
                             'and *_long.fastq.gz)')
    parser.add_argument('--fake_read_dir', type=str,
                        help='Directory containing read sets (named as *good_illumina_1.fastq.gz,'
                             '*bad_long.fastq.gz, etc.)')
    parser.add_argument('--ref_dir', type=str, required=False,
                        help='Directory containing reference FASTA files')
    parser.add_argument('--command_file', type=str, required=True,
                        help='Text file containing assembler commands')
    parser.add_argument('--out_dir', type=str, required=True,
                        help='Directory for assembly files and results table')

    args = parser.parse_args()

    if not args.real_read_dir and not args.fake_read_dir:
        sys.exit('You must supply either --real_read_dir or --fake_read_dir')
    if args.real_read_dir:
        if not os.path.isdir(args.real_read_dir):
            sys.exit('--real_read_dir must be a directory')
        args.real_read_dir = os.path.abspath(args.real_read_dir)
    if args.fake_read_dir:
        if not os.path.isdir(args.fake_read_dir):
            sys.exit('--fake_read_dir must be a directory')
        args.fake_read_dir = os.path.abspath(args.fake_read_dir)
    args.out_dir = os.path.abspath(args.out_dir)
    if args.ref_dir:
        args.ref_dir = os.path.abspath(args.ref_dir)

    return args


def create_results_table(out_dir):
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    results_table = os.path.join(out_dir, 'results.tsv')
    if os.path.isfile(results_table):
        return
    with open(results_table, 'wt') as table:
        empty_result = TestResult()
        table.write('\t'.join(list(empty_result.results.keys())))
        table.write('\n')


def group_real_reads(read_dir):
    read_filenames = [os.path.join(read_dir, f) for f in os.listdir(read_dir)
                      if os.path.isfile(os.path.join(read_dir, f)) and f.endswith('.fastq.gz')]

    read_sets = OrderedDict()
    for read_filename in read_filenames:
        set_name = get_set_name_from_real_read_filename(read_filename)
        if set_name not in read_sets:
            read_sets[set_name] = ReadSet(set_name, fake=False)
        read_full_filename = os.path.join(read_dir, read_filename)
        read_sets[set_name].add_read(read_full_filename)

    for read_set in read_sets.values():
        if read_set.get_set_type() == 'BAD':
            sys.exit('Read set ' + read_set.set_name + ' is incomplete')

    return list(read_sets.values())


def get_set_name_from_real_read_filename(read_filename):
    if read_filename.endswith('_1.fastq.gz'):
        set_name = read_filename[:-11]
    elif read_filename.endswith('_2.fastq.gz'):
        set_name = read_filename[:-11]
    elif read_filename.endswith('_long.fastq.gz'):
        set_name = read_filename[:-14]
    else:
        sys.exit('Bad filename: ' + read_filename + ' (read files must end with "_1.fastq.gz", '
                                                    '"_2.fastq.gz" or "_long.fastq.gz")')
    return set_name.split('/')[-1]


def group_fake_reads(read_dir):
    read_filenames = [os.path.join(read_dir, f) for f in os.listdir(read_dir)
                      if os.path.isfile(os.path.join(read_dir, f)) and f.endswith('.fastq.gz')]

    fake_read_sets = OrderedDict()
    for read_filename in read_filenames:
        set_name = get_set_name_from_fake_read_filename(read_filename)
        if set_name not in fake_read_sets:
            fake_read_sets[set_name] = FakeReadSet(set_name)
        read_full_filename = os.path.join(read_dir, read_filename)
        fake_read_sets[set_name].add_read(read_full_filename)

    read_sets = []
    for fake_read_set in fake_read_sets.values():
        read_sets += fake_read_set.get_read_sets()

    return read_sets


def get_set_name_from_fake_read_filename(read_filename):
    set_name = read_filename.split('_bad_')[0].split('_medium_')[0].split('_good_')[0]
    if set_name == read_filename:
        sys.exit('Bad filename: ' + read_filename)
    return set_name.split('/')[-1]


def execute_commands(commands, read_set, assembly_dir):
    if read_set.get_set_type() == 'short-only':
        set_commands = commands.get_short_read_assembly_commands(read_set)
    else:
        set_commands = commands.get_hybrid_assembly_commands(read_set)

    starting_dir = os.getcwd()
    os.chdir(assembly_dir)

    start_time = time.time()
    all_stdout = ''
    for command in set_commands:
        print(command, flush=True)
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   shell=True)
        stdout, _ = process.communicate()
        print('', flush=True)
        all_stdout += stdout.decode()
    assembly_time = time.time() - start_time

    os.chdir(starting_dir)
    return assembly_time, all_stdout


def evaluate_results(commands, read_set, assembly_dir, assembly_time, assembly_stdout, out_dir):
    result = TestResult()
    result.results['Read set name'] = read_set.set_name
    result.results['Read set type'] = read_set.get_set_type()

    result.results['Real or fake reads'] = read_set.real_or_fake()
    result.results['Fake Illumina read quality'] = read_set.fake_illumina_quality()
    result.results['Fake long read quality'] = read_set.fake_long_quality()

    result.results['Read files'] = read_set.get_read_list_str()

    if read_set.reference:
        result.results['Reference name'] = read_set.get_reference_name()
        ref_seqs = load_fasta(read_set.reference)
        lengths = [len(x[1]) for x in ref_seqs]
        result.results['Reference total length'] = str(sum(lengths))
        ref_count = len(ref_seqs)
        result.results['# reference sequences'] = str(len(ref_seqs))
        result.results['Reference sequence lengths'] = ', '.join([str(x) for x in lengths])
        result.results['Reference sequence depths'] = ', '.join([str(x[2]) for x in ref_seqs])
        result.results['Reference sequence circularity'] = ', '.join(['yes' if x[3] else 'no'
                                                                      for x in ref_seqs])
        longest_ref = max(lengths)
    else:
        ref_count = 0
        longest_ref = 0

    result.results['Assembler'] = commands.get_assembler_name()
    result.results['Assembler setting/output'] = commands.get_assembler_setting()
    result.results['Assembler version'] = commands.get_assembler_version()

    if read_set.get_set_type() == 'short-only':
        commands_str = '; '.join(commands.get_short_read_assembly_commands(read_set))
    else:
        commands_str = '; '.join(commands.get_hybrid_assembly_commands(read_set))
    result.results['Assembly command(s)'] = commands_str

    result.results['Assembly kmer size'] = commands.get_kmer_size()

    # Check to see that the final FASTA exists and contains sequence.
    final_fasta = os.path.join(assembly_dir, commands.final_assembly_fasta)
    if not os.path.isfile(final_fasta):
        failed = True
        print(red('assembly failed: ' + final_fasta + ' does not exist'))
    else:
        seqs = load_fasta(final_fasta)
        length = sum(len(x[1]) for x in seqs)
        if length == 0:
            failed = True
            print(red('assembly failed: ' + final_fasta + ' is empty'))
        elif length < 100000:
            failed = True
            print(red('assembly failed: ' + final_fasta + ' contains only ' +
                      str(length) + ' bp'))
        else:
            failed = False

    if failed:
        result.results['Assembly result'] = 'fail'
    else:
        result.results['Assembly result'] = 'success'
        print(green('assembly succeeded'))

    copied_fasta_name, copied_fasta = get_copied_fasta_name(read_set, commands, out_dir)
    assembly_stdout_filename = os.path.join(out_dir,
                                            copied_fasta_name.replace('.fasta', '.out'))
    with open(assembly_stdout_filename, 'wt') as assembly_stdout_file:
        assembly_stdout_file.write(assembly_stdout)
    print('OUTPUT ->', assembly_stdout_filename)

    if not failed:
        shutil.copy(final_fasta, copied_fasta)
        print(final_fasta, '->', copied_fasta)

        if commands.final_assembly_graph:
            final_graph = os.path.join(assembly_dir, commands.final_assembly_graph)
            if not os.path.isfile(final_graph):
                sys.exit('Error: could not find ' + final_graph)
            if final_graph.endswith('.gfa'):
                extension = 'gfa'
            elif final_graph.endswith('.fastg'):
                extension = 'fastg'
            else:
                sys.exit('Error: assembly graph must be gfa or fastg')
            copied_graph_name = copied_fasta_name.replace('.fasta', '.' + extension)
            copied_graph = os.path.join(out_dir, copied_graph_name)
            shutil.copy(final_graph, copied_graph)
            print(final_graph, '->', copied_graph)
        else:
            copied_graph = None

        result.results['Assembly time (seconds)'] = '%.1f' % assembly_time
        result.results['Assembly FASTA'] = copied_fasta.split('/')[-1]

        if copied_graph:
            result.results['Assembly graph'] = copied_graph.split('/')[-1]
            graph = unicycler.assembly_graph.AssemblyGraph(copied_graph, 0)
            dead_ends = graph.total_dead_end_count()
            result.results['Dead ends'] = dead_ends
            try:
                result.results['Percent dead ends'] = '%.2f' % (100.0 * dead_ends /
                                                                len(graph.segments))
            except ZeroDivisionError:
                pass

        run_quast(copied_fasta, read_set, out_dir, result)

        if read_set.reference:
            # Get total misassemblies in addition to extensive/local.
            extensive_misassemblies = int(result.results['# misassemblies'])
            local_misassemblies = int(result.results['# local misassemblies'])
            total_misassemblies = extensive_misassemblies + local_misassemblies
            result.results['Total misassemblies'] = str(total_misassemblies)

            # The assembly is considered complete if the number of contigs matches the reference
            # contig count and the largest contigs matches the largest reference to 10%.
            count_match = (ref_count == int(result.results['# contigs']))
            longest_contig_diff = abs(longest_ref - int(result.results['Largest contig']))
            try:
                longest_match = (longest_contig_diff / longest_ref < 0.1)
            except ZeroDivisionError:
                longest_match = False

            if count_match and longest_match:
                complete = 'yes'
            else:
                complete = 'no'
            result.results['Complete'] = complete

            # To be classed as 'Structurally perfect', the assembly needs no mistakes and nothing
            # extra (mismatches and small indels are still okay).
            unaligned_length = int(result.results['Unaligned length'])
            if complete == 'yes' and total_misassemblies == 0 and unaligned_length == 0 and \
                    float(result.results['Duplication ratio']) == 1.0:
                structurally_perfect = 'yes'
            else:
                structurally_perfect = 'no'
            result.results['Structurally perfect'] = structurally_perfect

            # To be classed as 'Completely perfect', the assembly needs no mistakes at all.
            mismatches = float(result.results['# mismatches per 100 kbp'])
            indels = float(result.results['# indels per 100 kbp'])
            ref_total_length = int(result.results['Reference total length'])
            assembly_total_length = int(result.results['Total length'])
            if structurally_perfect == 'yes' and mismatches == 0.0 and indels == 0.0 and \
                    ref_total_length == assembly_total_length:
                completely_perfect = 'yes'
            else:
                completely_perfect = 'no'
            result.results['Completely perfect'] = completely_perfect

    results_line = '\t'.join([str(x) for x in result.results.values()]) + '\n'
    results_table = os.path.join(out_dir, 'results.tsv')
    with open(results_table, 'at') as table:
        fcntl.flock(table, fcntl.LOCK_EX)
        table.write(results_line)
        fcntl.flock(table, fcntl.LOCK_UN)
    print()


def get_copied_fasta_name(read_set, commands, out_dir):

    copied_fasta_name = read_set.set_name + '__' + commands.get_assembler_name()
    setting = commands.get_assembler_setting()
    if setting:
        copied_fasta_name += '_' + setting
    copied_fasta_name += '_' + commands.get_assembler_version() + '.fasta'
    copied_fasta = os.path.join(out_dir, copied_fasta_name)
    return copied_fasta_name, copied_fasta


def run_quast(fasta, read_set, out_dir, result):
    quast_dir = os.path.join(out_dir, 'QUAST_TEMP_' + str(os.getpid()))

    quast_command = ['quast.py', fasta]

    if read_set.reference:
        quast_command += ['-R', read_set.reference]

    quast_command += ['-o', quast_dir,
                      '-l', '"' + read_set.set_name.replace(',', '') + '"',
                      '--no-plots', '--strict-NA']
    print()
    print(' '.join(quast_command))
    process = subprocess.Popen(quast_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _, _ = process.communicate()

    with open(os.path.join(quast_dir, 'report.tsv'), 'rt') as quast_report:
        for line in quast_report:
            line_parts = line.strip().split('\t')
            if line_parts[0] == 'Assembly':  # header line
                continue
            if not line_parts:
                continue
            if line_parts[0] in result.results:
                result.results[line_parts[0]] = line_parts[1]

    shutil.rmtree(quast_dir)


END_FORMATTING = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[93m'
DIM = '\033[2m'


def bold_yellow_underline(text):
    return YELLOW + BOLD + UNDERLINE + text + END_FORMATTING


def bold(text):
    return BOLD + text + END_FORMATTING


def red(text):
    return RED + text + END_FORMATTING


def green(text):
    return GREEN + text + END_FORMATTING


class ReadSet(object):
    def __init__(self, set_name, fake=False):
        self.set_name = set_name
        self.short_reads_1 = None
        self.short_reads_2 = None
        self.long_reads = None
        self.reference = None
        self.fake = fake

    def __repr__(self):
        return self.set_name + ' (' + self.get_set_type() + '): ' + self.get_read_list_str() + \
            ', reference: ' + self.get_reference_name()

    def get_read_list_str(self):
        read_files = [self.short_reads_1, self.short_reads_2, self.long_reads]
        return ', '.join(x.split('/')[-1] for x in read_files if x is not None)

    def add_read(self, read_filename):
        if read_filename is None:
            return
        if read_filename.endswith('_1.fastq.gz'):
            self.short_reads_1 = read_filename
        elif read_filename.endswith('_2.fastq.gz'):
            self.short_reads_2 = read_filename
        elif read_filename.endswith('_long.fastq.gz'):
            self.long_reads = read_filename

    def get_set_type(self):
        if self.short_reads_1 is None or self.short_reads_2 is None:
            return 'BAD'
        if self.long_reads is None:
            return 'short-only'
        else:
            return 'hybrid'

    def find_reference(self, ref_dir):
        # Only use a reference for fake read sets (where the 'truth' is exactly known).
        if not self.fake:
            return
        ref_filenames = [f for f in os.listdir(ref_dir)
                         if os.path.isfile(os.path.join(ref_dir, f)) and
                         (f.endswith('.fasta') or f.endswith('.fasta.gz'))]
        for ref_filename in ref_filenames:
            if ref_filename.split('.fasta')[0] in self.set_name:
                self.reference = os.path.join(ref_dir, ref_filename)
                break

    def get_reference_name(self):
        return 'None' if not self.reference else self.reference.split('/')[-1]

    def real_or_fake(self):
        if self.fake:
            return 'fake'
        else:
            return 'real'

    def fake_illumina_quality(self):
        if not self.fake:
            return ''
        return self.short_reads_1.split('_illumina')[0].split('_')[-1]

    def fake_long_quality(self):
        if not self.fake or not self.long_reads:
            return ''
        return self.long_reads.split('_long')[0].split('_')[-1]


class FakeReadSet(object):
    def __init__(self, set_name):
        self.set_name = set_name
        self.bad_short_reads_1 = None
        self.bad_short_reads_2 = None
        self.medium_short_reads_1 = None
        self.medium_short_reads_2 = None
        self.good_short_reads_1 = None
        self.good_short_reads_2 = None
        self.bad_long_reads = None
        self.medium_long_reads = None
        self.good_long_reads = None

    def add_read(self, read_filename):
        if read_filename.endswith('_bad_illumina_1.fastq.gz'):
            self.bad_short_reads_1 = read_filename
        elif read_filename.endswith('_bad_illumina_2.fastq.gz'):
            self.bad_short_reads_2 = read_filename
        elif read_filename.endswith('_medium_illumina_1.fastq.gz'):
            self.medium_short_reads_1 = read_filename
        elif read_filename.endswith('_medium_illumina_2.fastq.gz'):
            self.medium_short_reads_2 = read_filename
        elif read_filename.endswith('_good_illumina_1.fastq.gz'):
            self.good_short_reads_1 = read_filename
        elif read_filename.endswith('_good_illumina_2.fastq.gz'):
            self.good_short_reads_2 = read_filename
        elif read_filename.endswith('_bad_long.fastq.gz'):
            self.bad_long_reads = read_filename
        elif read_filename.endswith('_medium_long.fastq.gz'):
            self.medium_long_reads = read_filename
        elif read_filename.endswith('_good_long.fastq.gz'):
            self.good_long_reads = read_filename

    def get_read_sets(self):
        read_sets = []
        for short_qual in ['bad', 'medium', 'good']:
            short_read_set = ReadSet(self.set_name + '__' + short_qual + '_short', fake=True)
            if short_qual == 'bad':
                short_read_set.add_read(self.bad_short_reads_1)
                short_read_set.add_read(self.bad_short_reads_2)
            elif short_qual == 'medium':
                short_read_set.add_read(self.medium_short_reads_1)
                short_read_set.add_read(self.medium_short_reads_2)
            elif short_qual == 'good':
                short_read_set.add_read(self.good_short_reads_1)
                short_read_set.add_read(self.good_short_reads_2)
            if short_read_set.get_set_type() == 'short-only':
                read_sets.append(short_read_set)
            for long_qual in ['bad', 'medium', 'good']:
                hybrid_read_set = copy.deepcopy(short_read_set)
                hybrid_read_set.set_name += '__' + long_qual + '_long'
                if long_qual == 'bad':
                    hybrid_read_set.add_read(self.bad_long_reads)
                elif long_qual == 'medium':
                    hybrid_read_set.add_read(self.medium_long_reads)
                elif long_qual == 'good':
                    hybrid_read_set.add_read(self.good_long_reads)
                if hybrid_read_set.get_set_type() == 'hybrid':
                    read_sets.append(hybrid_read_set)

        sorted_read_sets = [x for x in read_sets if x.get_set_type() == 'short-only']
        sorted_read_sets += [x for x in read_sets if x.get_set_type() == 'hybrid']
        return sorted_read_sets


class Commands(object):
    def __init__(self, command_filename):
        self.short_read_assembly_commands = []
        self.hybrid_assembly_commands = []
        self.final_assembly_fasta = None
        self.final_assembly_graph = None
        self.command_filename = command_filename.split('/')[-1]

        final_assembly_files = []
        mode = None
        with open(command_filename, 'rt') as command_file:
            for line in command_file:
                line = line.strip()
                cleaned_line = line.split('#')[0].strip()
                if line == '# Short read assembly commands':
                    mode = 'SHORT'
                elif line == '# Hybrid assembly commands':
                    mode = 'HYBRID'
                elif line == '# Final assembly files':
                    mode = 'FINAL'
                elif not line:
                    mode = None
                else:
                    if mode == 'SHORT':
                        self.short_read_assembly_commands.append(cleaned_line)
                    if mode == 'HYBRID':
                        self.hybrid_assembly_commands.append(cleaned_line)
                    if mode == 'FINAL':
                        final_assembly_files.append(cleaned_line)

        short_or_hybrid = (bool(self.short_read_assembly_commands) or
                           bool(self.hybrid_assembly_commands))
        if not short_or_hybrid or not final_assembly_files:
            sys.exit('Bad command file')

        self.final_assembly_fasta = [x for x in final_assembly_files
                                     if x.endswith('.fasta') or x.endswith('.fa')][0]
        try:
            self.final_assembly_graph = [x for x in final_assembly_files
                                         if x.endswith('.gfa') or x.endswith('.fastg')][0]
        except IndexError:
            pass

    def get_short_read_assembly_commands(self, read_set):
        substituted_commands = []

        if read_set.reference:
            ref_seqs = load_fasta(read_set.reference)
            expected_linear_seqs = sum(0 if x[3] else 1 for x in ref_seqs)
            total_ref_length = sum(len(x[1]) for x in ref_seqs)
        else:
            expected_linear_seqs = 0
            total_ref_length = 5000000

        assembler_name = self.get_assembler_name()
        for line in self.short_read_assembly_commands:
            line = line.replace('SHORT_READS_1', read_set.short_reads_1)
            line = line.replace('SHORT_READS_2', read_set.short_reads_2)
            line = line.replace('GENOME_SIZE', str(total_ref_length))
            if assembler_name == 'Unicycler' and expected_linear_seqs:
                line += ' --expected_linear_seqs ' + str(expected_linear_seqs)
            substituted_commands.append(line)

        return substituted_commands

    def get_hybrid_assembly_commands(self, read_set):
        substituted_commands = []

        ref_seqs = load_fasta(read_set.reference)
        expected_linear_seqs = sum(0 if x[3] else 1 for x in ref_seqs)
        total_ref_length = sum(len(x[1]) for x in ref_seqs)
        assembler_name = self.get_assembler_name()

        for line in self.hybrid_assembly_commands:
            line = line.replace('SHORT_READS_1',  read_set.short_reads_1)
            line = line.replace('SHORT_READS_2', read_set.short_reads_2)
            line = line.replace('LONG_READS', read_set.long_reads)
            line = line.replace('GENOME_SIZE', str(total_ref_length))
            if assembler_name == 'Unicycler' and expected_linear_seqs:
                line += ' --expected_linear_seqs ' + str(expected_linear_seqs)
            substituted_commands.append(line)
        return substituted_commands

    def get_assembler_name(self):
        commands = ' '.join(self.short_read_assembly_commands) + ' '
        commands += ' '.join(self.hybrid_assembly_commands)
        if 'jsa.np.gapcloser' in commands or 'jsa.np.npscarf' in commands:
            return 'npScarf'
        elif 'unicycler' in commands:
            return 'Unicycler'
        elif 'abyss' in commands:
            return 'ABySS'
        elif 'spades' in commands:
            return 'SPAdes'
        elif 'velveth' in commands:
            return 'Velvet'
        elif commands.startswith('canu'):
            return 'Canu'
        else:
            return ''

    def get_assembler_setting(self):
        """
        Returns contigs/scaffolds for SPAdes and ABySS, and conservative/normal/bold for Unicycler.
        """
        assembler_name = self.get_assembler_name()
        if assembler_name == 'Unicycler':
            all_command_parts = []
            for line in self.short_read_assembly_commands:
                all_command_parts += line.split(' ')
            for line in self.hybrid_assembly_commands:
                all_command_parts += line.split(' ')
            all_command_str = ' '.join(all_command_parts)
            if 'mode bold' in all_command_str:
                return 'bold'
            elif 'mode conservative' in all_command_str:
                return 'conservative'
            else:
                return 'normal'
        elif assembler_name == 'SPAdes' or assembler_name == 'ABySS':
            if 'contigs' in self.final_assembly_fasta:
                return 'contigs'
            elif 'scaffolds' in self.final_assembly_fasta:
                return 'scaffolds'
            elif 'before_rr' in self.final_assembly_fasta:
                return 'before_rr'
        return ''

    def get_assembler_program(self):
        all_command_parts = []
        for line in self.short_read_assembly_commands:
            all_command_parts += line.split(' ')
        for line in self.hybrid_assembly_commands:
            all_command_parts += line.split(' ')
        assembler_name = self.get_assembler_name()
        if assembler_name == 'Unicycler':
            return [x for x in all_command_parts if 'unicycler' in x][0]
        elif assembler_name == 'SPAdes':
            return [x for x in all_command_parts if 'spades' in x][0]
        elif assembler_name == 'Velvet':
            return [x for x in all_command_parts if 'velveth' in x][0]
        elif assembler_name == 'npScarf':
            return [x for x in all_command_parts if 'jsa.np.gapcloser' in x][0]
        elif assembler_name == 'ABySS':
            return [x for x in all_command_parts if 'abyss' in x][0]
        elif assembler_name == 'Canu':
            return [x for x in all_command_parts if 'canu' in x][0]
        else:
            return ''

    def get_assembler_version(self):
        assembler_name = self.get_assembler_name()
        if assembler_name == 'Unicycler':
            version_command = self.get_assembler_program() + ' --version'
            process = subprocess.Popen(version_command, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, shell=True)
            stdout, stderr = process.communicate()
            all_out = stdout.decode() + ' ' + stderr.decode()
            return all_out.split('v')[1].split()[0]
        elif assembler_name == 'SPAdes':
            version_command = self.get_assembler_program() + ' --version'
            process = subprocess.Popen(version_command, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, shell=True)
            stdout, stderr = process.communicate()
            all_out = stdout.decode() + ' ' + stderr.decode()
            version = all_out.split(' v')[1].split()[0]
            if version.startswith('.'):
                version = version[1:]
            return version
        elif assembler_name == 'Velvet':
            version_command = self.get_assembler_program()
            process = subprocess.Popen(version_command, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, shell=True)
            stdout, stderr = process.communicate()
            all_out = stdout.decode() + ' ' + stderr.decode()
            return all_out.split('Version ')[1].split()[0]
        elif assembler_name == 'ABySS':
            process = subprocess.Popen('which abyss-pe', stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, shell=True)
            stdout, _ = process.communicate()
            abyss_path = stdout.decode().strip()
            if 'easybuild/software/ABySS/' in abyss_path:
                return abyss_path.split('easybuild/software/ABySS/')[1].split('-')[0]
            doc_path = os.path.abspath(abyss_path.replace('bin/abyss-pe', 'doc/abyss-pe.1'))
            with open(doc_path, 'rt') as doc_file:
                doc_data = doc_file.read()
            return doc_data.split('abyss-pe (ABySS) ')[1].split()[0].replace('"', '')
        elif assembler_name == 'Canu':
            version_command = self.get_assembler_program() + ' --version'
            process = subprocess.Popen(version_command, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, shell=True)
            stdout, stderr = process.communicate()
            all_out = stdout.decode() + ' ' + stderr.decode()
            return all_out.split('v')[1].split()[0]
        elif assembler_name == 'npScarf':
            version_command = self.get_assembler_program().replace('jsa.np.gapcloser', 'jsa')
            process = subprocess.Popen(version_command, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, shell=True)
            stdout, stderr = process.communicate()
            all_out = stdout.decode() + ' ' + stderr.decode()
            return all_out.split('Version ')[1].split(',')[0]

    def get_kmer_size(self):
        assembler_name = self.get_assembler_name()
        if assembler_name == 'Unicycler':
            return 'auto'
        elif assembler_name == 'SPAdes':
            return 'auto'
        elif assembler_name == 'Canu':
            return 'n/a'
        elif assembler_name == 'npScarf':
            return 'auto'
        commands = ' '.join(self.short_read_assembly_commands)
        if assembler_name == 'Velvet':
            return commands.split(' ')[2]
        elif assembler_name == 'ABySS':
            return commands.split('k=')[1].split()[0]
        return ''


class TestResult(object):
    def __init__(self):
        self.results = OrderedDict()
        self.results['Read set name'] = ''
        self.results['Read set type'] = ''
        self.results['Real or fake reads'] = ''
        self.results['Fake Illumina read quality'] = ''
        self.results['Fake long read quality'] = ''
        self.results['Read files'] = ''
        self.results['Reference name'] = ''
        self.results['Reference total length'] = ''
        self.results['# reference sequences'] = ''
        self.results['Reference sequence lengths'] = ''
        self.results['Reference sequence depths'] = ''
        self.results['Reference sequence circularity'] = ''
        self.results['Reference GC (%)'] = ''
        self.results['Assembler'] = ''
        self.results['Assembler setting/output'] = ''
        self.results['Assembler version'] = ''
        self.results['Assembly command(s)'] = ''
        self.results['Assembly kmer size'] = ''
        self.results['Assembly result'] = ''
        self.results['Assembly time (seconds)'] = ''
        self.results['Assembly FASTA'] = ''
        self.results['Assembly graph'] = ''
        self.results['# contigs (>= 0 bp)'] = ''
        self.results['# contigs (>= 1000 bp)'] = ''
        self.results['# contigs (>= 5000 bp)'] = ''
        self.results['# contigs (>= 10000 bp)'] = ''
        self.results['# contigs (>= 25000 bp)'] = ''
        self.results['# contigs (>= 50000 bp)'] = ''
        self.results['Total length (>= 0 bp)'] = ''
        self.results['Total length (>= 1000 bp)'] = ''
        self.results['Total length (>= 5000 bp)'] = ''
        self.results['Total length (>= 10000 bp)'] = ''
        self.results['Total length (>= 25000 bp)'] = ''
        self.results['Total length (>= 50000 bp)'] = ''
        self.results['# contigs'] = ''
        self.results['Largest contig'] = ''
        self.results['Total length'] = ''
        self.results['GC (%)'] = ''
        self.results['N50'] = ''
        self.results['NG50'] = ''
        self.results['N75'] = ''
        self.results['NG75'] = ''
        self.results['L50'] = ''
        self.results['LG50'] = ''
        self.results['L75'] = ''
        self.results['LG75'] = ''
        self.results['# misassemblies'] = ''
        self.results['# misassembled contigs'] = ''
        self.results['Misassembled contigs length'] = ''
        self.results['# local misassemblies'] = ''
        self.results['Total misassemblies'] = ''
        self.results['# unaligned mis. contigs'] = ''
        self.results['# unaligned contigs'] = ''
        self.results['Unaligned length'] = ''
        self.results['Genome fraction (%)'] = ''
        self.results['Duplication ratio'] = ''
        self.results["# N's per 100 kbp"] = ''
        self.results['# mismatches per 100 kbp'] = ''
        self.results['# indels per 100 kbp'] = ''
        self.results['Largest alignment'] = ''
        self.results['Total aligned length'] = ''
        self.results['NA50'] = ''
        self.results['NGA50'] = ''
        self.results['NA75'] = ''
        self.results['NGA75'] = ''
        self.results['LA50'] = ''
        self.results['LGA50'] = ''
        self.results['LA75'] = ''
        self.results['LGA75'] = ''
        self.results['Dead ends'] = ''
        self.results['Percent dead ends'] = ''
        self.results['Complete'] = ''
        self.results['Structurally perfect'] = ''
        self.results['Completely perfect'] = ''


if __name__ == '__main__':
    main()
