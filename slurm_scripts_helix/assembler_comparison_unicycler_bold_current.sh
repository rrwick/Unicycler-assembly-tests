#!/bin/bash
#SBATCH -p sysgen
#SBATCH --nodes=1
#SBATCH --job-name="Unicycler bold current version assembler comparison"
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32762
#SBATCH --time=10-0:0:00

module load SAMtools/1.3.1-vlsci_intel-2015.08.25-HTSlib-1.3.1
module load Bowtie2/2.2.9-vlsci_intel-2015.08.25
module load Java/1.8.0_60
module load BLAST+/2.2.30-vlsci_intel-2015.08.25-Python-2.7.10
module load Python/3.5.2-vlsci_intel-2015.08.25

export PATH="/vlsci/SG0006/rwick/SPAdes-3.9.1-Linux/bin:$PATH"
export PATH="/vlsci/SG0006/rwick/Unicycler:$PATH"
export PATH="/vlsci/SG0006/rwick/quast-4.4:$PATH"
export PATH="/scratch/sysgen/rwick/Unicycler-assembly-tests:$PATH"

COMMAND_FILE="/scratch/sysgen/rwick/Unicycler-assembly-tests/assembly_commands/unicycler_bold"

READ_DIR="/scratch/sysgen/rwick/Unicycler-assembly-tests/synthetic_reads"
OUT_DIR="/scratch/sysgen/rwick/assembly_test_results"
REF_DIR="/scratch/sysgen/rwick/Unicycler-assembly-tests/reference_sequences"

cd $OUT_DIR

assembler_comparison-runner.py --fake_read_dir $READ_DIR/Streptococcus_suis_BM407 --command_file $COMMAND_FILE --out_dir $OUT_DIR --ref_dir $REF_DIR
assembler_comparison-runner.py --fake_read_dir $READ_DIR/random_sequences_no_repeats --command_file $COMMAND_FILE --out_dir $OUT_DIR --ref_dir $REF_DIR
assembler_comparison-runner.py --fake_read_dir $READ_DIR/random_sequences_some_repeats --command_file $COMMAND_FILE --out_dir $OUT_DIR --ref_dir $REF_DIR
assembler_comparison-runner.py --fake_read_dir $READ_DIR/random_sequences_many_repeats --command_file $COMMAND_FILE --out_dir $OUT_DIR --ref_dir $REF_DIR
assembler_comparison-runner.py --fake_read_dir $READ_DIR/Acinetobacter_AB30 --command_file $COMMAND_FILE --out_dir $OUT_DIR --ref_dir $REF_DIR
assembler_comparison-runner.py --fake_read_dir $READ_DIR/Mycobacterium_tuberculosis_H37Rv --command_file $COMMAND_FILE --out_dir $OUT_DIR --ref_dir $REF_DIR
assembler_comparison-runner.py --fake_read_dir $READ_DIR/E_coli_K-12_MG1655 --command_file $COMMAND_FILE --out_dir $OUT_DIR --ref_dir $REF_DIR
assembler_comparison-runner.py --fake_read_dir $READ_DIR/E_coli_O25b_H4-ST131 --command_file $COMMAND_FILE --out_dir $OUT_DIR --ref_dir $REF_DIR
assembler_comparison-runner.py --fake_read_dir $READ_DIR/Klebsiella_NTUH-K2044 --command_file $COMMAND_FILE --out_dir $OUT_DIR --ref_dir $REF_DIR
assembler_comparison-runner.py --fake_read_dir $READ_DIR/Klebsiella_30660_NJST258_1 --command_file $COMMAND_FILE --out_dir $OUT_DIR --ref_dir $REF_DIR
assembler_comparison-runner.py --fake_read_dir $READ_DIR/Klebsiella_MGH_78578 --command_file $COMMAND_FILE --out_dir $OUT_DIR --ref_dir $REF_DIR
assembler_comparison-runner.py --fake_read_dir $READ_DIR/Shigella_sonnei_53G --command_file $COMMAND_FILE --out_dir $OUT_DIR --ref_dir $REF_DIR
assembler_comparison-runner.py --fake_read_dir $READ_DIR/Shigella_dysenteriae_Sd197 --command_file $COMMAND_FILE --out_dir $OUT_DIR --ref_dir $REF_DIR
assembler_comparison-runner.py --fake_read_dir $READ_DIR/Acinetobacter_A1 --command_file $COMMAND_FILE --out_dir $OUT_DIR --ref_dir $REF_DIR
assembler_comparison-runner.py --fake_read_dir $READ_DIR/Saccharomyces_cerevisiae_S288c --command_file $COMMAND_FILE --out_dir $OUT_DIR --ref_dir $REF_DIR