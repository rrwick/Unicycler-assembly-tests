# Unicycler assembly tests

This repository contains tools for evaluating the performance of bacterial genome assemblers.



### Generating synthetic Illumina reads

The `generate_illumina_reads` script is a wrapper for the [ART](https://www.niehs.nih.gov/research/resources/software/biostatistics/art/) program. It adds two bits of functionality to ART:
* If a sequence has `circular=true` in its FASTA header, this script will run ART at multiple sequence rotations to ensure that the simulated reads seamlessly cover the whole circular sequence.
* Sequences can have `depth=X` in their FASTA header, where `X` is a number. This script will adjust the number of reads generated from each sequence in the FASTA to preserve the relative depths. This is mainly used for plasmid sequences which should be more represented in the reads than the chromosomal sequence.

##### Quality presets

`--good` is equivalent to `--depth 40.0 --platform HS10_100` and will generate 100 bp reads with low and uneven depth. The resulting assembly graphs may contain many dead ends due to areas missing coverage.

`--medium` is equivalent to `--depth 45.0 --platform HS25_125` and will generate 125 bp reads. The depth will probably be sufficient to cover the entire genome.

`--good` is equivalent to `--depth 80.0 --platform MSv3_250` and will generate 250 bp reads with abundant depth.



### Generating synthetic long reads

The `generate_long_reads` script uses PBSIM to generate long reads. It adds the same functionality for circular sequences and differing depths as the `generate_illumina_reads` script. Additionally, it uses a log-normal distribution to choose sequence lengths and a beta distribution to choose sequence identities.

##### Quality presets

`--good_nanopore` is equivalent to `--length 20000 --id_alpha 13 --id_beta 2 --id_max 0.98`

`--medium_nanopore` is equivalent to `--length 10000 --id_alpha 12 --id_beta 3 --id_max 0.95`

`--bad_nanopore` is equivalent to `--length 5000 --id_alpha 11 --id_beta 4 --id_max 0.9`

`--good_pacbio` is equivalent to `--length 20000 --id_alpha 90 --id_beta 10 --id_max 1.0`

`--medium_pacbio` is equivalent to `--length 10000 --id_alpha 85 --id_beta 15 --id_max 1.0`

`--bad_pacbio` is equivalent to `--length 5000 --id_alpha 75 --id_beta 25 --id_max 1.0`



