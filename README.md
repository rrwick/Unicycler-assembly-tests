# Unicycler assembly tests

This repository contains tools for evaluating the performance of bacterial genome assemblers and resulting data. I made these to test my hybrid assembler [Unicycler](https://github.com/rrwick/Unicycler), both to compare it against other assemblers and to assess its performance as I further develop it.

The raw table of assembly data is available in `results.tsv`.

This repo is still a work in progress! Check back later for more results!


# Table of contents

* [Programs tested](#metrics)
* [Metrics](#metrics)
* [Assembly of synthetic short reads](#assembly-of-synthetic-short-reads)
     * [Averages over all short read sets](#averages-over-all-short-read-sets)
     * [Averages over bad short read sets](#averages-over-bad-short-read-sets)
     * [Averages over medium short read sets](#averages-over-medium-short-read-sets)
     * [Averages over good short read sets](#averages-over-good-short-read-sets)
     * [SPAdes performance by version](#spades-performance-by-version)
     * [ABySS performance by version](#abyss-performance-by-version)
     * [Unicycler performance by version](#unicycler-performance-by-version)
* [Assembly of synthetic hybrid read sets](#assembly-of-synthetic-hybrid-read-sets)
     * [Averages over all hybrid read sets](#averages-over-all-hybrid-read-sets)
     * [Averages over bad short read sets](#averages-over-bad-short-read-sets-1)
     * [Averages over medium short read sets](#averages-over-medium-short-read-sets-1)
     * [Averages over good short read sets](#averages-over-good-short-read-sets-1)
     * [Averages over bad long read sets](#averages-over-bad-long-read-sets)
     * [Averages over medium long read sets](#averages-over-medium-long-read-sets)
     * [Averages over good long read sets](#averages-over-good-long-read-sets)
     * [SPAdes performance by version](#spades-performance-by-version-1)
     * [npScarf performance by version](#npscarf-performance-by-version)
     * [Unicycler performance by version](#unicycler-performance-by-version-1)
* [Tools](#tools)
     * [Generating synthetic Illumina reads](#generating-synthetic-illumina-reads)
     * [Generating synthetic long reads](#generating-synthetic-long-reads)
     * [Running test assemblies](#running-test-assemblies)


# Programs tested

[Unicycler](https://github.com/rrwick/Unicycler) for both short read and hybrid assemblies. I ran it in each of its three modes: conservative, normal and bold.

[SPAdes](http://cab.spbu.ru/software/spades/) for both short read and hybrid assemblies. Both `contigs.fasta` and `scaffolds.fasta` are analysed. For short read assemblies, I also included `before_rr.fasta` which corresponds to `assembly_graph.fastg`. SPAdes was run with the `--careful` options as suggested in the [SPAdes manual](http://cab.spbu.ru/files/release3.9.1/manual.html#sec3.4) for small genomes.

[npScarf](https://github.com/mdcao/npScarf) for hybrid assemblies.

[ABySS](https://github.com/bcgsc/abyss) for short read assemblies. Both `*-contigs.fa` and `*-scaffolds.fa` are analysed. ABySS needs a k-mer size as a parameter, so I used `k=64` as shown in their example for [assembling a paired-end library](https://github.com/bcgsc/abyss#assembling-a-paired-end-library).

[Velvet](https://www.ebi.ac.uk/~zerbino/velvet/) for short read assemblies. Like ABySS, Velvet needs a k-mer. To match the ABySS assemblies, I used a k-mer of 63 (Velvet k-mers must be odd).

[VelvetOptimiser](https://github.com/tseemann/VelvetOptimiser) for short read assemblies. I used a very wide k-mer sweep, from 19 to 101 (slow but thorough).

For the exact commands, check out the files in the [assembly_commands/](assembly_commands/) directory.


# Metrics

I ran [QUAST 4.4](http://quast.bioinf.spbau.ru/) on each assembly, which generates many metrics you can read about in the [QUAST manual](http://quast.bioinf.spbau.ru/manual.html). Below are some quick explanations of the few I chose to focus on here:

__N50__: A well-known metric of contig sizes. Contigs of this size and larger comprise at least half of the assembly. This metric measures only how big the contigs are, not whether they are correct. E.g. it is possible to 'cheat' your way to a large N50 score by aggressively combining sequences which shouldn't be combined.

__NGA50__: This is like N50, but instead of being based on contig sizes, it is based on QUAST's alignments of contigs to the reference genome. Since a misassembled contig can have multiple smaller alignments, this metric does penalise for assembly errors. I think of it as like an N50 score where you can't 'cheat'. For these tests, QUAST was run with the `--strict-NA` option which makes it break alignments on both local and extensive misassemblies (the default is to only break on extensive misassemblies).

__Misassemblies__: QUAST categories misassemblies as either local (less than 1 kbp discrepancy) or extensive (more than 1 kbp discrepancy). This metric is a sum of the two. I.e. it is a count of all misassemblies, regardless of their size.

__Small error rate__: QUAST counts both mismatch and indel rates, and this metric is a sum of the two. Indels counted here are small, because if they were too large they would instead be a misassembly.

__Assembly time__: How many minutes the assembly took to complete. These tests were all run with 8 cores, but the conditions weren't very controlled, so these values won't be too precise.



# Assembly of synthetic short reads

Short reads were generated at three different quality levels: bad, medium and good (see [Generating synthetic Illumina reads](#generating-synthetic-illumina-reads) for more information).


### Bad short read sets


### Medium short read sets


### Good short read sets



# Assembly of synthetic hybrid read sets

The hybrid read sets use the same synthetic Illumina reads as described above (three quality levels). Long reads were also generated at three quality levels (see [Generating synthetic long reads](#generating-synthetic-long-reads) for more information).

All nine combinations of short and long reads sets were assembled: bad/bad, bad/medium, bad/good, medium/bad, medium/medium, medium/good, good/bad, good/medium and good/good.


### Bad short, bad long hybrid read sets


### Bad short, medium long hybrid read sets


### Bad short, good long hybrid read sets


### Medium short, bad long hybrid read sets


### Medium short, medium long hybrid read sets


### Medium short, good long hybrid read sets


### Good short, bad long hybrid read sets


### Good short, medium long hybrid read sets


### Good short, good long hybrid read sets



# Conclusions



# Tools

These the scripts included in this repo

### Generating synthetic Illumina reads

`generate_illumina_reads` is a wrapper for the [ART](https://www.niehs.nih.gov/research/resources/software/biostatistics/art/) program. It adds two bits of functionality to ART:
* If a sequence has `circular=true` in its FASTA header, this script will run ART at multiple sequence rotations to ensure that the simulated reads seamlessly cover the whole circular sequence.
* Sequences can have `depth=X` in their FASTA header, where `X` is a number. This script will adjust the number of reads generated from each sequence in the FASTA to preserve the relative depths. This is mainly used for plasmid sequences which should be more represented in the reads than the chromosomal sequence.

##### Quality presets

`--bad` is equivalent to `--depth 40.0 --platform HS10_100` and will generate 100 bp reads with low and uneven depth. The resulting assembly graph may contain many dead ends due to areas missing coverage.

`--medium` is equivalent to `--depth 40.0 --platform HS25_125` and will generate 125 bp reads. The depth will probably be sufficient to cover the entire genome.

`--good` is equivalent to `--depth 100.0 --platform HS25_150` and will generate 150 bp reads with abundant depth.


### Generating synthetic long reads

`generate_long_reads` uses PBSIM to generate long reads. It adds the same functionality for circular sequences and differing depths as the `generate_illumina_reads` script. It uses a log-normal distribution to choose sequence lengths and a beta distribution to choose sequence identities.

##### Quality presets

`--good_nanopore` is equivalent to `--length 20000 --id_alpha 13 --id_beta 2 --id_max 0.98`

`--medium_nanopore` is equivalent to `--length 10000 --id_alpha 12 --id_beta 3 --id_max 0.95`

`--bad_nanopore` is equivalent to `--length 5000 --id_alpha 11 --id_beta 4 --id_max 0.9`

`--good_pacbio` is equivalent to `--length 20000 --id_alpha 90 --id_beta 10 --id_max 1.0`

`--medium_pacbio` is equivalent to `--length 10000 --id_alpha 85 --id_beta 15 --id_max 1.0`

`--bad_pacbio` is equivalent to `--length 5000 --id_alpha 75 --id_beta 25 --id_max 1.0`


### Running test assemblies

`assembler_comparison` is a program which gathers up read sets, assembles them using a text file of assembly commands and runs [QUAST](quast.bioinf.spbau.ru) to assess the results.

