declare -a REFERENCES=("Acinetobacter_A1" "Acinetobacter_AB30" "E_coli_K-12_MG1655" "E_coli_O25b_H4-ST131" "Klebsiella_30660_NJST258_1" "Klebsiella_MGH_78578" "Klebsiella_NTUH-K2044" "Mycobacterium_tuberculosis_H37Rv" "Saccharomyces_cerevisiae_S288c" "Shigella_dysenteriae_Sd197" "Shigella_sonnei_53G" "Streptococcus_suis_BM407" "random_sequences_no_repeats" "random_sequences_some_repeats" "random_sequences_many_repeats")

# Make fake Illumina reads (three different qualities) for each reference.
for REF in "${REFERENCES[@]}"; do
  generate_illumina_reads --bad --reference ../reference_sequences/"$REF".fasta.gz -1 "$REF"_bad_illumina_1.fastq -2 "$REF"_bad_illumina_2.fastq
  generate_illumina_reads --medium --reference ../reference_sequences/"$REF".fasta.gz -1 "$REF"_medium_illumina_1.fastq -2 "$REF"_medium_illumina_2.fastq
  generate_illumina_reads --good --reference ../reference_sequences/"$REF".fasta.gz -1 "$REF"_good_illumina_1.fastq -2 "$REF"_good_illumina_2.fastq
done

# Make fake long reads (three different qualities) for each reference.
for REF in "${REFERENCES[@]}"; do
  generate_long_reads --bad_nanopore --depth 8.0 --reference ../reference_sequences/"$REF".fasta.gz -l "$REF"_bad_long.fastq
  generate_long_reads --medium_nanopore --depth 16.0 --reference ../reference_sequences/"$REF".fasta.gz -l "$REF"_medium_long.fastq
  generate_long_reads --good_nanopore --depth 32.0 --reference ../reference_sequences/"$REF".fasta.gz -l "$REF"_good_long.fastq
done

# Compress the reads with zopfli. This is slow but should make the files about 10% smaller than gzip would.
for FASTQ in *.fastq; do
  zopfli -c $FASTQ > $FASTQ.gz
  rm $FASTQ
done
