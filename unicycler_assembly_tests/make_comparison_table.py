#!/usr/bin/env python3

from collections import OrderedDict
import argparse
import statistics
import sys


def main():
    args = get_arguments()
    include_list = [x.split(',') for x in args.include.split(';')]
    headers, results = load_table(args.results)

    print()
    print('Assemblies in full table:  ', len(results))

    if args.type:
        results = [x for x in results if x['Read set type'] == args.type]
    if args.illumina_qual:
        results = [x for x in results if x['Fake Illumina read quality'] == args.illumina_qual]
    if args.long_qual:
        results = [x for x in results if x['Fake long read quality'] == args.long_qual]
    results = [x for x in results if x['Assembly result'] == 'success']
    results = [x for x in results if any(record_matches_include(x, y) for y in include_list)]
    results = filter_results_for_read_sets(results, include_list)

    print('Assemblies passing filters:', len(results))
    print()
    if not results:
        sys.exit('Error: no assembies passed the filters')
    read_sets = set(x['Read set name'] for x in results)
    print('Read sets passing filters: ', len(read_sets))
    for read_set in read_sets:
        print('  ' + read_set)
    print()


    markdown_table = [['Assembler', 'Setting/output', 'Version', 'N50', 'NGA50', 'Misassemblies', 'Small errors per 100 kbp', 'Time']]
    for include in include_list:
        row = [include[0], include[1], include[2],
               '%.0f' % get_mean(results, include, 'N50'),
               '%.0f' % get_mean(results, include, 'NGA50'),
               '%.2f' % get_mean(results, include, 'Total misassemblies'),
               '%.2f' % get_mean(results, include, '# small errors per 100 kbp'),
               '%.2f' % get_mean(results, include, 'Assembly time (minutes)')]
        markdown_table.append(row)
    print_table(markdown_table)
    print()

    write_table(headers, results, args.out)


def get_arguments():
    parser = argparse.ArgumentParser(description='Make comparison table')
    parser.add_argument('--results', type=str, required=True, help='Full table of results')
    parser.add_argument('--type', type=str, help='short-only or hybrid')
    parser.add_argument('--illumina_qual', type=str, help='bad, medium or good')
    parser.add_argument('--long_qual', type=str, help='bad, medium or good')
    parser.add_argument('--include', type=str, help='semi-colon delimited list of assembler,setting,version to include (Example: Unicycler,normal,0.2.0;SPAdes,contigs,3.9.1)')
    parser.add_argument('--out', type=str, required=True, help='Output table')

    return parser.parse_args()


def load_table(results_filename):
    records = []
    with open(results_filename, 'rt') as results:
        for line in results:
            line_parts = line.strip().split('\t')
            if not line_parts:
                continue
            if line_parts[0] == 'Read set name':
                headers = line_parts
                headers += ['# small errors per 100 kbp', 'Assembly time (minutes)']
                continue
            record = OrderedDict()
            for i, header in enumerate(headers):
                try:
                    record[header] = line_parts[i]
                except IndexError:
                    record[header] = ''
            try:
                record['# small errors per 100 kbp'] = str(float(record["# N's per 100 kbp"]) + float(record['# mismatches per 100 kbp']) + float(record['# indels per 100 kbp']))
            except ValueError:
                record['# small errors per 100 kbp'] = ''
            try:
                record['Assembly time (minutes)'] = str(float(record['Assembly time (seconds)']) / 60)
            except ValueError:
                record['Assembly time (minutes)'] = ''
            records.append(record)
    return headers, records


def write_table(headers, results, out_filename):
    with open(out_filename, 'wt') as out_file:
        out_file.write('\t'.join(headers))
        out_file.write('\n')
        for record in results:
            out_file.write('\t'.join(record.values()))
            out_file.write('\n')


def filter_results_for_read_sets(results, include_list):
    all_read_sets = set(x['Read set name'] for x in results)
    passing_read_sets = set()
    for read_set in all_read_sets:
        read_set_records = [x for x in results if x['Read set name'] == read_set]
        matches_for_each_include = True
        for include in include_list:
            if not any(record_matches_include(x, include) for x in read_set_records):
                matches_for_each_include = False
        if matches_for_each_include:
            passing_read_sets.add(read_set)
    return [x for x in results if x['Read set name'] in passing_read_sets]


def record_matches_include(record, include):
    assembler, setting, version = include
    return record['Assembler'] == assembler and record['Assembler setting/output'] == setting and record['Assembler version'] == version


def get_mean(results, include, metric):
    records = [x for x in results if record_matches_include(x, include)]
    values = [float(x[metric]) for x in records]
    return statistics.mean(values)


def print_table(table):
    column_count = len(table[0])
    table = [x[:column_count] for x in table]
    table = [x + [''] * (column_count - len(x)) for x in table]
    col_widths = [0] * column_count
    for row in table:
        col_widths = [max(col_widths[i], len(x)) for i, x in enumerate(row)]
    separator = ' | '

    for i, row in enumerate(table):
        aligned_row = []
        for j, value in enumerate(row):
            if j < 3:
                aligned_row.append(value.ljust(col_widths[j]))
            else:
                aligned_row.append(value.rjust(col_widths[j]))
        print('| ' + separator.join(aligned_row) + ' |')
        if i == 0:
            line = []
            for j, _ in enumerate(row):
                if j < 3:
                    line.append(':' + '-' * (col_widths[j] - 1))
                else:
                    line.append('-' * (col_widths[j] - 1) + ':')
            print('| ' + separator.join(line) + ' |')


if __name__ == '__main__':
    main()
