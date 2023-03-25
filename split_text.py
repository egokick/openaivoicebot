import sys

def split_text_file(input_file: str, max_words: int = 100):
    with open(input_file, 'r') as infile:
        words = infile.read().split()

    word_count = len(words)
    num_files = (word_count + max_words - 1) // max_words
    output_prefix = input_file.rsplit('.', 1)[0]

    for i in range(num_files):
        start = i * max_words
        end = min((i + 1) * max_words, word_count)
        output_file = f"{output_prefix}_{i + 1}.txt"

        with open(output_file, 'w') as outfile:
            outfile.write(" ".join(words[start:end]))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python split_text.py <input_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    split_text_file(input_file)
