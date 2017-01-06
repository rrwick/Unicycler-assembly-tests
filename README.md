# Unicycler assembly tests

This repository contains tools for evaluating the performance of bacterial genome assemblers and resulting data. I made these to test my hybrid assembler [Unicycler](https://github.com/rrwick/Unicycler), both to compare it against other assemblers and to assess its performance as I further develop it.

The raw table of assembly data is available in `results.tsv`.

This repo is still a work in progress! Check back later for more results!


# Table of contents

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



# Metrics

__N50__: 

__NGA50__: 

__Ext. mis.__: 

__Local mis.__: 

__Small error rate__: 

__Assembly time__: 


# Assembly of synthetic short reads

Short reads were generated at three different quality levels: bad, medium and good (see [Generating synthetic Illumina reads](#generating-synthetic-illumina-reads) for more information).

### Averages over all short read sets

Assembler | N50 | NGA50 | Ext. mis. | Local mis. | Small error rate | Assembly time
--- | --- | --- | --- | --- | --- | ---
Velvet (v1.2.10) | - | - | - | - | - | -
SPAdes (v3.9.1) before RR | - | - | - | - | - | -
SPAdes (v3.9.1) contigs | - | - | - | - | - | -
SPAdes (v3.9.1) scaffolds | - | - | - | - | - | -
ABySS (v2.0.2) contigs | - | - | - | - | - | -
ABySS (v2.0.2) scaffolds | - | - | - | - | - | -
Unicycler (v0.2) conservative | - | - | - | - | - | -
Unicycler (v0.2) normal | - | - | - | - | - | -
Unicycler (v0.2) bold | - | - | - | - | - | -


### Averages over bad short read sets


### Averages over medium short read sets


### Averages over good short read sets


### SPAdes performance by version


### ABySS performance by version


### Unicycler performance by version


# Assembly of synthetic hybrid read sets

The hybrid read sets use the same synthetic Illumina reads as described above (three quality levels). Long reads were also generated at three quality levels (see [Generating synthetic long reads](#generating-synthetic-long-reads) for more information).

All nine combinations of short and long reads sets were assembled: bad/bad, bad/medium, bad/good, medium/bad, medium/medium, medium/good, good/bad, good/medium and good/good.


### Averages over all hybrid read sets


### Averages over bad short read sets


### Averages over medium short read sets


### Averages over good short read sets


### Averages over bad long read sets


### Averages over medium long read sets


### Averages over good long read sets


### SPAdes performance by version


### npScarf performance by version


### Unicycler performance by version



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

