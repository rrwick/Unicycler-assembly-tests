# Unicycler assembly tests

This repository contains tools for evaluating the performance of bacterial genome assemblers and resulting data. I made these to test [Unicycler](https://github.com/rrwick/Unicycler) - both to compare it against other assemblers and to assess its performance as I develop it.

The raw table of all data is available in [assembly_data.tsv] and some interesting summary tables are below.

This repo is still a work in progress! Check back later for more results!



# Table of contents

* [Programs tested](#programs-tested)
* [Metrics](#metrics)
* [Reference genomes](#reference-genomes)
* [Synthetic reads](#synthetic-reads)
* [Assembly of synthetic short reads](#assembly-of-synthetic-short-reads)
    * [Bad short reads](#bad-short-reads)
    * [Medium short reads](#medium-short-reads)
    * [Good short reads](#good-short-reads)
* [Assembly of synthetic hybrid read sets](#assembly-of-synthetic-hybrid-read-sets)
    * [Bad short, bad long](#bad-short-bad-long)
    * [Bad short, medium long](#bad-short-medium-long)
    * [Bad short, good long](#bad-short-good-long)
    * [Medium short, bad long](#medium-short-bad-long)
    * [Medium short, medium long](#medium-short-medium-long)
    * [Medium short, good long](#medium-short-good-long)
    * [Good short, bad long](#good-short-bad-long)
    * [Good short, medium long](#good-short-medium-long)
    * [Good short, good long](#good-short-good-long)
* [Conclusions](#conclusions)
* [Tools](#tools)
    * [Generating synthetic Illumina reads](#generating-synthetic-illumina-reads)
    * [Generating synthetic long reads](#generating-synthetic-long-reads)
    * [Running test assemblies](#running-test-assemblies)



# Programs tested

* [Unicycler](https://github.com/rrwick/Unicycler) for both short read and hybrid assemblies. I ran it in each of its three modes: conservative, normal and bold.
* [SPAdes](http://cab.spbu.ru/software/spades/) for both short read and hybrid assemblies. Both `contigs.fasta` and `scaffolds.fasta` are analysed. For short read assemblies, I also included `before_rr.fasta` which corresponds to `assembly_graph.fastg`. SPAdes was run with the `--careful` options as suggested in the [SPAdes manual](http://cab.spbu.ru/files/release3.9.1/manual.html#sec3.4) for small genomes.
* [npScarf](https://github.com/mdcao/npScarf) for hybrid assemblies. I used SPAdes to make the input contigs, and npScarf can be run using just the contigs or with with SPAdes assembly graph as additional info. Both configurations (with and without the SPAdes assembly graph) are analysed.
* [ABySS](https://github.com/bcgsc/abyss) for short read assemblies. Both `*-contigs.fa` and `*-scaffolds.fa` are analysed. ABySS needs a k-mer size as a parameter, so I used `k=64` as shown in their example for [assembling a paired-end library](https://github.com/bcgsc/abyss#assembling-a-paired-end-library).
* [Velvet](https://www.ebi.ac.uk/~zerbino/velvet/) for short read assemblies. Like ABySS, Velvet needs a k-mer. To match the ABySS assemblies, I used a k-mer of 63 (Velvet k-mers must be odd).
* [VelvetOptimiser](https://github.com/tseemann/VelvetOptimiser) for short read assemblies. I used a very wide k-mer sweep, from 19 to 101 (slow but thorough).
* [Canu](http://canu.readthedocs.io/en/latest/) and [Pilon](https://github.com/broadinstitute/pilon/wiki) for hybrid assemblies. This approach uses the long reads alone to create the assembly and then polishes it with the short reads.

For the exact commands, check out the files in the [assembly_commands/](assembly_commands/) directory.



# Metrics

I ran [QUAST 4.4](http://quast.bioinf.spbau.ru/) on each assembly, which generates many metrics you can read about in the [QUAST manual](http://quast.bioinf.spbau.ru/manual.html). Below are some quick explanations of the few I chose to focus on here:

* __Successes__: The number of times the assembler successfully completed the assembly over the number of attempted assemblies. Assemblers could fail due to a crash or due to exceeding memory requirements (up to 64 GB was available for these tests).
* __N50__: A well-known metric of contig sizes. Contigs of this size and larger comprise at least half of the assembly. This metric measures only how big the contigs are, not whether they are correct. E.g. it is possible to 'cheat' your way to a large N50 score by aggressively combining sequences which shouldn't be combined.
* __NGA50__: This is like N50, but instead of being based on contig sizes, it is based on QUAST's alignments of contigs to the reference genome. Since a misassembled contig can have multiple smaller alignments, this metric does penalise for assembly errors. I think of it as like an N50 score where you can't 'cheat'. For these tests, QUAST was run with the `--strict-NA` option which makes it break alignments on both local and extensive misassemblies (the default is to only break on extensive misassemblies).
* __Misassemblies__: QUAST categories misassemblies as either local (less than 1 kbp discrepancy) or extensive (more than 1 kbp discrepancy). This metric is a sum of the two (i.e. a count of all misassemblies, regardless of their size).
* __Small error rate__: QUAST counts both mismatch and indel rates, and this metric is a sum of the two. Indels counted here are small, because large indels will instead register as a misassembly. As in the QUAST results, these are expressed as a count per 100 kpb.
* __Assembly time__: How many minutes the assembly took to complete. These tests were all run with 8 cores, but the conditions weren't very controlled, so these times won't be too precise.

To give an accurate comparison between assemblers, the tables below show the average values for the read sets _completed by all assemblers_. E.g. if if assembler A completed all 45/45 read sets, assembler B completed 44/45 (failed on one) and assembler C completed 44/45 (failed on a different one), then the table will show averages for the 43 read sets completed by all assemblers.



# Reference genomes

Three references are artificial bacterial genomes:
* __random sequences, no repeats__: a 4 Mb chromosome, 100 kb plasmid and 10 kb plasmid, all made of random bases. With no repeats of any significant length, this is the easiest genome to assemble.
* __random sequences, some repeats__: The same three replicon sizes but with a moderate amount of repeats added.
* __random sequences, many repeats__: The same three replicon sizes but with a large number of repeats added.

Twelve references are assemblies available from [NCBI](https://www.ncbi.nlm.nih.gov/):
* [_Acinetobacter baumannii_ A1](https://www.ncbi.nlm.nih.gov/assembly/248731/): has a large, repetitive biofilm-associated protein gene that's difficult to assemble
* [_Acinetobacter baumannii_ AB30](https://www.ncbi.nlm.nih.gov/assembly/206901/): has a large, repetitive biofilm-associated protein gene that's difficult to assemble
* [_Escherichia coli_ K-12 MG1655](https://www.ncbi.nlm.nih.gov/assembly/79781)
* [_Escherichia coli_ O25b:H4-ST131 EC958](https://www.ncbi.nlm.nih.gov/assembly/319101)
* [_Klebsiella pneumoniae_ 30660/NJST258_1](https://www.ncbi.nlm.nih.gov/assembly/131541): lots of plasmids
* [_Klebsiella pneumoniae_ MGH 78578](https://www.ncbi.nlm.nih.gov/assembly/37408/): lots of plasmids
* [_Klebsiella pneumoniae_ NTUH-K2044](https://www.ncbi.nlm.nih.gov/assembly/31388/)
* [_Mycobacterium tuberculosis_ H37Rv](https://www.ncbi.nlm.nih.gov/assembly/538048): Lots of PE and PPE genes, moderately difficult to assemble.
* [_Saccharomyces cerevisiae_ S288c](https://www.ncbi.nlm.nih.gov/assembly/285498): the only eurkaryote genome included - haploid with 16 linear chromosomes and a circular mitochondrial chromosome
* [_Shigella dysenteriae_ Sd197](https://www.ncbi.nlm.nih.gov/assembly/33108/): has lots of insertion sequences and is difficult to assemble
* [_Shigella sonnei_ 53G](https://www.ncbi.nlm.nih.gov/assembly/406998): has lots of insertion sequences and is difficult to assemble
* [_Streptococcus suis_ BM407](https://www.ncbi.nlm.nih.gov/assembly/45668/)



# Synthetic reads

The read files are too large for this GitHub repo, but you can download them here: [https://cloudstor.aarnet.edu.au/plus/index.php/s/dzRCaxLjpGpfKYW](https://cloudstor.aarnet.edu.au/plus/index.php/s/dzRCaxLjpGpfKYW)



# Assembly of synthetic short reads

Short reads were synthesised at three different qualities: bad, medium and good (see [synthetic Illumina read quality presets](#quality-presets)).


### Bad short reads

| Assembler              | Setting/output | Successes |    N50 | NGA50 | Misassemblies | Small error rate | Time |
| :--------------------- | :------------- | --------: | -----: | ----: | ------------: | ---------------: | ---: |
| Velvet v1.2.10         |                |           |        |       |               |                  |      |
| VelvetOptimiser v2.2.5 |                |           |        |       |               |                  |      |
| ABySS v2.0.2           | contigs        |           |        |       |               |                  |      |
| ABySS v2.0.2           | scaffolds      |           |        |       |               |                  |      |
| SPAdes v3.9.1          | contigs        |           |        |       |               |                  |      |
| SPAdes v3.9.1          | scaffolds      |           |        |       |               |                  |      |
| Unicycler v0.2.0       | conservative   |           |        |       |               |                  |      |
| Unicycler v0.2.0       | normal         |           |        |       |               |                  |      |
| Unicycler v0.2.0       | bold           |           |        |       |               |                  |      |


### Medium short reads

| Assembler              | Setting/output | Successes |    N50 | NGA50 | Misassemblies | Small error rate | Time |
| :--------------------- | :------------- | --------: | -----: | ----: | ------------: | ---------------: | ---: |
| Velvet v1.2.10         |                |           |        |       |               |                  |      |
| VelvetOptimiser v2.2.5 |                |           |        |       |               |                  |      |
| ABySS v2.0.2           | contigs        |           |        |       |               |                  |      |
| ABySS v2.0.2           | scaffolds      |           |        |       |               |                  |      |
| SPAdes v3.9.1          | contigs        |           |        |       |               |                  |      |
| SPAdes v3.9.1          | scaffolds      |           |        |       |               |                  |      |
| Unicycler v0.2.0       | conservative   |           |        |       |               |                  |      |
| Unicycler v0.2.0       | normal         |           |        |       |               |                  |      |
| Unicycler v0.2.0       | bold           |           |        |       |               |                  |      |


### Good short reads

| Assembler              | Setting/output | Successes |    N50 | NGA50 | Misassemblies | Small error rate | Time |
| :--------------------- | :------------- | --------: | -----: | ----: | ------------: | ---------------: | ---: |
| Velvet v1.2.10         |                |           |        |       |               |                  |      |
| VelvetOptimiser v2.2.5 |                |           |        |       |               |                  |      |
| ABySS v2.0.2           | contigs        |           |        |       |               |                  |      |
| ABySS v2.0.2           | scaffolds      |           |        |       |               |                  |      |
| SPAdes v3.9.1          | contigs        |           |        |       |               |                  |      |
| SPAdes v3.9.1          | scaffolds      |           |        |       |               |                  |      |
| Unicycler v0.2.0       | conservative   |           |        |       |               |                  |      |
| Unicycler v0.2.0       | normal         |           |        |       |               |                  |      |
| Unicycler v0.2.0       | bold           |           |        |       |               |                  |      |



# Assembly of synthetic hybrid read sets

The hybrid read sets use the same synthetic Illumina reads as described above (three quality levels). Long reads were also synthesised at three qualites (see [synthetic long read quality presets](#quality-presets-1)).

All nine combinations of short and long reads sets were assembled: bad/bad, bad/medium, bad/good, medium/bad, medium/medium, medium/good, good/bad, good/medium and good/good.


### Bad short, bad long

| Assembler         | Setting/output | Successes |    N50 | NGA50 | Misassemblies | Small error rate | Time |
| :---------------- | :------------- | --------: | -----: | ----: | ------------: | ---------------: | ---: |
| SPAdes v3.9.1     | contigs        |           |        |       |               |                  |      |
| SPAdes v3.9.1     | scaffolds      |           |        |       |               |                  |      |
| npScarf v1.6‑10a  | from contigs   |           |        |       |               |                  |      |
| npScarf v1.6‑10a  | with graph     |           |        |       |               |                  |      |
| Canu v1.4 + Pilon |                |           |        |       |               |                  |      |
| Unicycler v0.2.0  | conservative   |           |        |       |               |                  |      |
| Unicycler v0.2.0  | normal         |           |        |       |               |                  |      |
| Unicycler v0.2.0  | bold           |           |        |       |               |                  |      |


### Bad short, medium long

| Assembler         | Setting/output | Successes |    N50 | NGA50 | Misassemblies | Small error rate | Time |
| :---------------- | :------------- | --------: | -----: | ----: | ------------: | ---------------: | ---: |
| SPAdes v3.9.1     | contigs        |           |        |       |               |                  |      |
| SPAdes v3.9.1     | scaffolds      |           |        |       |               |                  |      |
| npScarf v1.6‑10a  | from contigs   |           |        |       |               |                  |      |
| npScarf v1.6‑10a  | with graph     |           |        |       |               |                  |      |
| Canu v1.4 + Pilon |                |           |        |       |               |                  |      |
| Unicycler v0.2.0  | conservative   |           |        |       |               |                  |      |
| Unicycler v0.2.0  | normal         |           |        |       |               |                  |      |
| Unicycler v0.2.0  | bold           |           |        |       |               |                  |      |


### Bad short, good long

| Assembler         | Setting/output | Successes |    N50 | NGA50 | Misassemblies | Small error rate | Time |
| :---------------- | :------------- | --------: | -----: | ----: | ------------: | ---------------: | ---: |
| SPAdes v3.9.1     | contigs        |           |        |       |               |                  |      |
| SPAdes v3.9.1     | scaffolds      |           |        |       |               |                  |      |
| npScarf v1.6‑10a  | from contigs   |           |        |       |               |                  |      |
| npScarf v1.6‑10a  | with graph     |           |        |       |               |                  |      |
| Canu v1.4 + Pilon |                |           |        |       |               |                  |      |
| Unicycler v0.2.0  | conservative   |           |        |       |               |                  |      |
| Unicycler v0.2.0  | normal         |           |        |       |               |                  |      |
| Unicycler v0.2.0  | bold           |           |        |       |               |                  |      |


### Medium short, bad long

| Assembler         | Setting/output | Successes |    N50 | NGA50 | Misassemblies | Small error rate | Time |
| :---------------- | :------------- | --------: | -----: | ----: | ------------: | ---------------: | ---: |
| SPAdes v3.9.1     | contigs        |           |        |       |               |                  |      |
| SPAdes v3.9.1     | scaffolds      |           |        |       |               |                  |      |
| npScarf v1.6‑10a  | from contigs   |           |        |       |               |                  |      |
| npScarf v1.6‑10a  | with graph     |           |        |       |               |                  |      |
| Canu v1.4 + Pilon |                |           |        |       |               |                  |      |
| Unicycler v0.2.0  | conservative   |           |        |       |               |                  |      |
| Unicycler v0.2.0  | normal         |           |        |       |               |                  |      |
| Unicycler v0.2.0  | bold           |           |        |       |               |                  |      |


### Medium short, medium long

| Assembler         | Setting/output | Successes |    N50 | NGA50 | Misassemblies | Small error rate | Time |
| :---------------- | :------------- | --------: | -----: | ----: | ------------: | ---------------: | ---: |
| SPAdes v3.9.1     | contigs        |           |        |       |               |                  |      |
| SPAdes v3.9.1     | scaffolds      |           |        |       |               |                  |      |
| npScarf v1.6‑10a  | from contigs   |           |        |       |               |                  |      |
| npScarf v1.6‑10a  | with graph     |           |        |       |               |                  |      |
| Canu v1.4 + Pilon |                |           |        |       |               |                  |      |
| Unicycler v0.2.0  | conservative   |           |        |       |               |                  |      |
| Unicycler v0.2.0  | normal         |           |        |       |               |                  |      |
| Unicycler v0.2.0  | bold           |           |        |       |               |                  |      |


### Medium short, good long

| Assembler         | Setting/output | Successes |    N50 | NGA50 | Misassemblies | Small error rate | Time |
| :---------------- | :------------- | --------: | -----: | ----: | ------------: | ---------------: | ---: |
| SPAdes v3.9.1     | contigs        |           |        |       |               |                  |      |
| SPAdes v3.9.1     | scaffolds      |           |        |       |               |                  |      |
| npScarf v1.6‑10a  | from contigs   |           |        |       |               |                  |      |
| npScarf v1.6‑10a  | with graph     |           |        |       |               |                  |      |
| Canu v1.4 + Pilon |                |           |        |       |               |                  |      |
| Unicycler v0.2.0  | conservative   |           |        |       |               |                  |      |
| Unicycler v0.2.0  | normal         |           |        |       |               |                  |      |
| Unicycler v0.2.0  | bold           |           |        |       |               |                  |      |


### Good short, bad long

| Assembler         | Setting/output | Successes |    N50 | NGA50 | Misassemblies | Small error rate | Time |
| :---------------- | :------------- | --------: | -----: | ----: | ------------: | ---------------: | ---: |
| SPAdes v3.9.1     | contigs        |           |        |       |               |                  |      |
| SPAdes v3.9.1     | scaffolds      |           |        |       |               |                  |      |
| npScarf v1.6‑10a  | from contigs   |           |        |       |               |                  |      |
| npScarf v1.6‑10a  | with graph     |           |        |       |               |                  |      |
| Canu v1.4 + Pilon |                |           |        |       |               |                  |      |
| Unicycler v0.2.0  | conservative   |           |        |       |               |                  |      |
| Unicycler v0.2.0  | normal         |           |        |       |               |                  |      |
| Unicycler v0.2.0  | bold           |           |        |       |               |                  |      |


### Good short, medium long

| Assembler         | Setting/output | Successes |    N50 | NGA50 | Misassemblies | Small error rate | Time |
| :---------------- | :------------- | --------: | -----: | ----: | ------------: | ---------------: | ---: |
| SPAdes v3.9.1     | contigs        |           |        |       |               |                  |      |
| SPAdes v3.9.1     | scaffolds      |           |        |       |               |                  |      |
| npScarf v1.6‑10a  | from contigs   |           |        |       |               |                  |      |
| npScarf v1.6‑10a  | with graph     |           |        |       |               |                  |      |
| Canu v1.4 + Pilon |                |           |        |       |               |                  |      |
| Unicycler v0.2.0  | conservative   |           |        |       |               |                  |      |
| Unicycler v0.2.0  | normal         |           |        |       |               |                  |      |
| Unicycler v0.2.0  | bold           |           |        |       |               |                  |      |


### Good short, good long

| Assembler         | Setting/output | Successes |    N50 | NGA50 | Misassemblies | Small error rate | Time |
| :---------------- | :------------- | --------: | -----: | ----: | ------------: | ---------------: | ---: |
| SPAdes v3.9.1     | contigs        |           |        |       |               |                  |      |
| SPAdes v3.9.1     | scaffolds      |           |        |       |               |                  |      |
| npScarf v1.6‑10a  | from contigs   |           |        |       |               |                  |      |
| npScarf v1.6‑10a  | with graph     |           |        |       |               |                  |      |
| Canu v1.4 + Pilon |                |           |        |       |               |                  |      |
| Unicycler v0.2.0  | conservative   |           |        |       |               |                  |      |
| Unicycler v0.2.0  | normal         |           |        |       |               |                  |      |
| Unicycler v0.2.0  | bold           |           |        |       |               |                  |      |



# Conclusions



# Tools

These the scripts included in this repo that I used to generate the reads and run the assembly tests.

### Generating synthetic Illumina reads

`generate_illumina_reads` is a wrapper for the [ART](https://www.niehs.nih.gov/research/resources/software/biostatistics/art/) program. It adds two bits of functionality to ART:
* If a sequence has `circular=true` in its FASTA header, this script will run ART at multiple sequence rotations to ensure that the simulated reads seamlessly cover the whole circular sequence.
* Sequences can have `depth=X` in their FASTA header, where `X` is a number. This script will adjust the number of reads generated from each sequence in the FASTA to preserve the relative depths. This is mainly used for plasmid sequences which should be more represented in the reads than the chromosomal sequence.

##### Quality presets

* `--bad` is equivalent to `--depth 40.0 --platform HS10_100` and will generate 100 bp reads with low and uneven depth. The resulting assembly graph may contain many dead ends due to areas missing coverage.
* `--medium` is equivalent to `--depth 40.0 --platform HS25_125` and will generate 125 bp reads. The depth will probably be even enough to cover the entire genome.
* `--good` is equivalent to `--depth 100.0 --platform HS25_150` and will generate 150 bp reads with abundant and even depth.


### Generating synthetic long reads

`generate_long_reads` uses PBSIM to generate long reads. It adds the same functionality for circular sequences and differing depths as the `generate_illumina_reads` script. It uses a log-normal distribution to choose sequence lengths and a beta distribution to choose sequence identities.

##### Quality presets

Nanopore presets have a wider distribution of read identity; PacBio presets have a narrow identity distribution. For the tests above I used the Nanopore presets.

* `--bad_nanopore` is equivalent to `--depth 8.0 --length 5000 --id_alpha 11 --id_beta 4 --id_max 0.9`
* `--medium_nanopore` is equivalent to `--depth 16.0 --length 10000 --id_alpha 12 --id_beta 3 --id_max 0.95`
* `--good_nanopore` is equivalent to `--depth 32.0 --length 20000 --id_alpha 13 --id_beta 2 --id_max 0.98`
* `--bad_pacbio` is equivalent to `--depth 8.0 --length 5000 --id_alpha 75 --id_beta 25 --id_max 1.0`
* `--medium_pacbio` is equivalent to `--depth 16.0 --length 10000 --id_alpha 85 --id_beta 15 --id_max 1.0`
* `--good_pacbio` is equivalent to `--depth 32.0 --length 20000 --id_alpha 90 --id_beta 10 --id_max 1.0`

The depths are on the low side. I.e. if you used a full PacBio SMRT Cell or Nanopore flow cell for one bacterial isolate, you'd probably get higher depth than these presets give. These depths instead simulate what you might get if you multiplex multiple bacterial isolates together: lower depth but lower cost.


### Running test assemblies

`assembler_comparison` is a program which gathers up read sets, assembles them using a text file of assembly commands and runs [QUAST](quast.bioinf.spbau.ru) to assess the results.

