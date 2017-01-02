"""
This is a tool for assembling read sets (short-only or hybrid) using different assemblers.

Reads must be named such that

Author: Ryan Wick
email: rrwick@gmail.com
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from collections import OrderedDict


def main():
    args = get_arguments()
    read_sets = group_reads(os.path.abspath(args.read_dir))
    commands = Commands(args.command_file)
    assembly_dir = os.path.abspath('ASSEMBLY_TEMP_' + str(os.getpid()))
    if not os.path.isfile(args.results_table):
        create_results_table(args.results_table)

    for read_set in read_sets:
        os.makedirs(assembly_dir)
        assembly_time = execute_commands(commands, read_set, assembly_dir)
        evaluate_results(commands, read_set, assembly_dir, assembly_time)
        shutil.rmtree(assembly_dir)


def get_arguments():
    parser = argparse.ArgumentParser(description='Assembler comparison tool')
    parser.add_argument('--read_dir', type=str, required=True,
                        help='Directory containing read sets (named as *_1.fastq.gz, *_2.fastq.gz '
                             'and *_long.fastq.gz)')
    parser.add_argument('--ref_dir', type=str, required=False,
                        help='Directory containing reference FASTA files')
    parser.add_argument('--run_name', type=str, required=True,
                        help='Name for this assembly run')
    parser.add_argument('--command_file', type=str, required=True,
                        help='Text file containing assembler commands')
    parser.add_argument('--results_table', type=str, required=True,
                        help='File to contain assembly results')

    args = parser.parse_args()

    if not os.path.isdir(args.read_dir):
        sys.exit('--read_dir must be a directory')
    args.read_dir = os.path.abspath(args.read_dir)
    args.results_table = os.path.abspath(args.results_table)

    return args


def create_results_table(results_table):
    with open(results_table, 'wt') as table:
        empty_result = TestResult()
        table.write('\t'.join(list(empty_result.results.keys())))
        table.write('\n')


def group_reads(read_dir):
    read_filenames = [os.path.join(read_dir, f) for f in os.listdir(read_dir)
                      if os.path.isfile(os.path.join(read_dir, f)) and f.endswith('.fastq.gz')]

    read_sets = OrderedDict()
    for read_filename in read_filenames:
        set_name = get_set_name_from_read_filename(read_filename)
        if set_name not in read_sets:
            read_sets[set_name] = ReadSet(set_name)
        read_full_filename = os.path.join(read_dir, read_filename)
        read_sets[set_name].add_read(read_full_filename)

    for read_set in read_sets.values():
        if read_set.get_set_type() == 'BAD':
            sys.exit('Read set ' + read_set.set_name + ' is incomplete')

    return list(read_sets.values())


def get_set_name_from_read_filename(read_filename):
    if read_filename.endswith('_1.fastq.gz'):
        set_name = read_filename[:-11]
    elif read_filename.endswith('_2.fastq.gz'):
        set_name = read_filename[:-11]
    elif read_filename.endswith('_long.fastq.gz'):
        set_name = read_filename[:-14]
    else:
        sys.exit('Read files must end with "_1.fastq.gz", "_2.fastq.gz" or "_long.fastq.gz"')
    return set_name.split('/')[-1]


def execute_commands(commands, read_set, assembly_dir):
    if read_set.get_set_type() == 'SHORT':
        set_commands = commands.get_short_read_assembly_commands(read_set)
    else:
        set_commands = commands.get_hybrid_assembly_commands(read_set)

    starting_dir = os.getcwd()
    os.chdir(assembly_dir)

    print()
    print(bold_yellow_underline('Read set: ' + read_set.set_name))

    start_time = time.time()
    for command in set_commands:
        print(command)
        subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        print()
    assembly_time = time.time() - start_time

    os.chdir(starting_dir)
    return assembly_time


def evaluate_results(commands, read_set, assembly_dir, assembly_time):
    pass

    # TO DO
    # TO DO
    # TO DO
    # TO DO
    # TO DO
    # TO DO
    # TO DO
    # TO DO
    # TO DO
    # TO DO
    # TO DO
    # TO DO
    # TO DO
    # TO DO
    # TO DO
    # TO DO
    # TO DO


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


class ReadSet(object):
    def __init__(self, set_name):
        self.set_name = set_name
        self.short_reads_1 = None
        self.short_reads_2 = None
        self.long_reads = None

    def add_read(self, read_filename):
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
            return 'SHORT'
        else:
            return 'HYBRID'


class Commands(object):
    def __init__(self, command_filename):
        self.short_read_assembly_commands = []
        self.hybrid_assembly_commands = []
        self.final_assembly_files = []

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
                        self.final_assembly_files.append(cleaned_line)

        short_or_hybrid = (bool(self.short_read_assembly_commands) or
                           bool(self.hybrid_assembly_commands))
        if not short_or_hybrid or not self.final_assembly_files:
            sys.exit('Bad command file')

    def get_short_read_assembly_commands(self, read_set):
        substituted_commands = []
        for line in self.short_read_assembly_commands:
            line = line.replace('SHORT_READS_1',read_set.short_reads_1)
            line = line.replace('SHORT_READS_2',read_set.short_reads_2)
            substituted_commands.append(line)
        return substituted_commands

    def get_hybrid_assembly_commands(self, read_set):
        substituted_commands = []
        for line in self.hybrid_assembly_commands:
            line = line.replace('SHORT_READS_1',read_set.short_reads_1)
            line = line.replace('SHORT_READS_2',read_set.short_reads_2)
            line = line.replace('LONG_READS',read_set.long_reads)
            substituted_commands.append(line)
        return substituted_commands


class TestResult(object):
    def __init__(self, test_name=''):
        self.results = OrderedDict()
        self.results['Test name'] = test_name
        self.results['Read set name'] = ''
        self.results['Assembly command'] = ''
        self.results['Assembly time'] = ''
        self.results['Contigs'] = ''
        self.results['Largest contig'] = ''
        self.results['Total length'] = ''
        self.results['Reference length'] = ''
        self.results['N50'] = ''
        self.results['NG50'] = ''
        self.results['N75'] = ''
        self.results['NG75'] = ''
        self.results['L50'] = ''
        self.results['LG50'] = ''
        self.results['L75'] = ''
        self.results['LG75'] = ''
        self.results['Misassemblies'] = ''
        self.results['Misassembled contigs length'] = ''
        self.results['Local misassemblies'] = ''
        self.results['Unaligned contigs'] = ''
        self.results['Unaligned length'] = ''
        self.results['Genome fraction'] = ''
        self.results['Duplication ratio'] = ''
        self.results['Ns per 100 kbp'] = ''
        self.results['Mismatches per 100 kbp'] = ''
        self.results['Indels per 100 kbp'] = ''
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
        self.results['Complete'] = ''
        self.results['Perfect'] = ''


if __name__ == '__main__':
    main()
