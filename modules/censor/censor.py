import os
import re

import yaml

cwd = os.getcwd()
# module_path = os.path.join(cwd, "modules", "censor")
# with open(os.path.join(module_path, "bad_words.yaml"), "r") as bad_words_file:
#     bad_words = yaml.safe_load(bad_words_file)


# Determine if a word matches a bad word
def bad_match(word):
    if word in bad_words:
        return True

    word_match = ''
    # Replace all non-text characters with .s
    for i, char in enumerate(word):
        if ord('a') <= ord(char) <= ord('z'):
            word_match += char + '[a-z]{0,1}'
            continue
        word_match += '[a-z]{0,2}'

    # Regex matching
    for bad_word in bad_words:
        # Match length limit
        length_limit = len(bad_word)-1
        if len(bad_word) < 5:
            length_limit += 1

        match = re.match(word_match, bad_word)
        if not match:
            continue
        if len(match.group()) > length_limit:
            print(bad_word, word_match)
            return True
    return False


def running_check(letters, length):
    flags = []
    for i in range(len(letters)-length):
        substring = letters[i:i+length]
        if bad_match(substring):
            flags += (i, i+length)
    return flags


def censor_sentence(sentence):
    # First, check every word
    words = list(sentence.split(' '))
    for i, word in enumerate(words):
        if bad_match(word):
            words[i] = '*' * len(word)

    # Then, check consecutive letters
    # This may be too strong of a filter for certain applications.
#    letters = sentence.replace(' ', '').replace('\n', '')
#    for i in range(3, 6):
#        flags = running_check(letters, i)
#        for trigger in flags:
#            sentence

    new_sentence = ''
    for word in words:
        for char in word:
            if ord('a') <= ord(char) <= ord('z'):
                new_sentence += char
            elif ord('A') <= ord(char) <= ord('Z'):
                new_sentence += char
            elif ord('0') <= ord(char) <= ord('9'):
                new_sentence += char
            elif char in (',', '.', '!', '?', '-', '(', ')', '&', '"', "'", '/', ':', ';', '*'):
                new_sentence += char
        new_sentence += ' '

    return new_sentence
        

if __name__ == '__main__':
    with open(os.path.join(os.getcwd(), "bad_words.yaml"), "r") as bad_words_file:
        bad_words = yaml.safe_load(bad_words_file)
    print(censor_sentence('hi everyone this nigg will present you all with this fucker'))
