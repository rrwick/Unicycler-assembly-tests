import random


def get_random_base():
    rand_int = random.randint(0, 3)
    if rand_int == 0:
        return 'A'
    elif rand_int == 1:
        return 'C'
    elif rand_int == 2:
        return 'G'
    elif rand_int == 3:
        return 'T'


def get_random_sequence(length):
    sequence = ''
    for _ in range(length):
        sequence += get_random_base()
    return sequence


def add_line_breaks_to_sequence(sequence, line_length):
    if not sequence:
        return '\n'
    seq_with_breaks = ''
    pos = 0
    while pos < len(sequence):
        seq_with_breaks += sequence[pos:pos+line_length] + '\n'
        pos += line_length
    return seq_with_breaks


seq1 = get_random_sequence(4000000)
seq2 = get_random_sequence(100000)
seq3 = get_random_sequence(10000)
random_ref = open('random_sequences_no_repeats.fasta' ,'wt')
random_ref.write('>chromosome depth=1.0 circular=true\n')
random_ref.write(add_line_breaks_to_sequence(seq1, 70))
random_ref.write('>plasmid_1 depth=1.2 circular=true\n')
random_ref.write(add_line_breaks_to_sequence(seq2, 70))
random_ref.write('>plasmid_3 depth=8.0 circular=true\n')
random_ref.write(add_line_breaks_to_sequence(seq3, 70))
random_ref.close()


def reverse_complement(seq):
    return ''.join([complement_base(seq[i]) for i in range(len(seq) - 1, -1, -1)])


def complement_base(base):
    if base == 'A':
        return 'T'
    if base == 'T':
        return 'A'
    if base == 'G':
        return 'C'
    if base == 'C':
        return 'G'
    if base == 'a':
        return 't'
    if base == 't':
        return 'a'
    if base == 'g':
        return 'c'
    if base == 'c':
        return 'g'
    forward = 'RYSWKMryswkmBDHVbdhvNn.-?'
    reverse = 'YRSWMKyrswmkVHDBvhdbNn.-?N'
    return reverse[forward.find(base)]


def make_repeaty_sequence(length, repeat_count, max_instances):
    seq = get_random_sequence(length)
    for i in range(repeat_count):
        repeat_length = random.randint(1, 50) ** 2
        repeat_instances = random.randint(2, 10)
        repeat_seq = get_random_sequence(repeat_length)
        for j in range(repeat_instances):
            if random.randint(0, 1) == 1:
                repeat_seq = reverse_complement(repeat_seq)
            repeat_pos = random.randint(0, length-repeat_length)
            if random.randint(0, 1) == 0:  # Sometimes the repeat replaces the current sequence.
                seq = seq[:repeat_pos] + repeat_seq + seq[repeat_pos + repeat_length:]
            else:  # Sometimes the repeat inserts into the current sequence.
                seq = seq[:repeat_pos] + repeat_seq + seq[repeat_pos:]
                seq = seq[:length]
            assert len(seq) == length
    return seq


seq = make_repeaty_sequence(4110000, 12, 10)
seq1 = seq[:4000000]
seq2 = seq[4000000:4100000]
seq3 = seq[4100000:4110000]
random_ref = open('random_sequences_some_repeats.fasta' ,'wt')
random_ref.write('>chromosome depth=1.0 circular=true\n')
random_ref.write(add_line_breaks_to_sequence(seq1, 70))
random_ref.write('>plasmid_1 depth=1.2 circular=true\n')
random_ref.write(add_line_breaks_to_sequence(seq2, 70))
random_ref.write('>plasmid_3 depth=8.0 circular=true\n')
random_ref.write(add_line_breaks_to_sequence(seq3, 70))
random_ref.close()

seq = make_repeaty_sequence(4110000, 50, 100)
seq1 = seq[:4000000]
seq2 = seq[4000000:4100000]
seq3 = seq[4100000:4110000]
random_ref = open('random_sequences_many_repeats.fasta' ,'wt')
random_ref.write('>chromosome depth=1.0 circular=true\n')
random_ref.write(add_line_breaks_to_sequence(seq1, 70))
random_ref.write('>plasmid_1 depth=1.2 circular=true\n')
random_ref.write(add_line_breaks_to_sequence(seq2, 70))
random_ref.write('>plasmid_3 depth=8.0 circular=true\n')
random_ref.write(add_line_breaks_to_sequence(seq3, 70))
random_ref.close()
