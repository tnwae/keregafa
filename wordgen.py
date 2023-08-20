#!/usr/bin/env python3

import conlang_utils as cu
import json
import numpy as np
from typing import Union
import re

reduplicatep = True


class WordBuilder:

    def __init__(self, ruletab: str):
        self.conlang_data = cu.ConlangData(ruletab)
        self.results = set()

    def run(self, count: int, mode: int, length: int):
        while len(self.results) < count:
            if length == 0:
                word_length = np.random.choice(
                    list(
                        range(
                            1, len(wb.conlang_data.syllable_count_probabilities
                                   ))),
                    p=wb.conlang_data.syllable_count_probabilities[1:])
            else:
                word_length = length

            wb.make_word(word_length, mode)

    def make_word(self,
                  syllable_count: int = 0,
                  mode: Union[str, None] = None) -> None:
        temp = ""
        created_word = []
        result = []

        if syllable_count == 1:
            temp = "I"
        elif syllable_count == 2:
            temp = "IF"
        else:
            temp = np.random.choice(
                list(self.conlang_data.word_types.keys()),
                1,
                p=list(self.conlang_data.word_types.values()))[0]

        try:
            syllables = [
                self.conlang_data.compile_syllable_class(ch) for ch in temp
            ]
        except Exception as ex:
            print(f"{ex} (temp: {temp})")

        for syllable in syllables:
            for ch in list(syllable):
                created_word.append(self.conlang_data.compile_char(ch))

        gen = (letter for letter in created_word
               if self.conlang_data.is_vowel(letter))
        self.conlang_data.harmonize(created_word, next(gen))

        result.append("".join(created_word))

        reduplicated = self.conlang_data.reduplicate_word(created_word)

        if reduplicated:
            result.append("".join(reduplicated))

        if self.conlang_data.replacement_rules:
            for rule, filters in self.conlang_data.replacement_rules.items():
                for filter, target in filters.items():
                    for i in range(0, len(result)):
                        result[i] = re.sub(filter, target, result[i])

        [self.results.add(w) for w in result]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser("wordgen")
    parser.add_argument("-r",
                        "--ruletab",
                        help="rule table file",
                        type=str,
                        default="./keregafa.json")
    parser.add_argument("-c",
                        "--count",
                        help="number of words to generate",
                        type=int,
                        default=1)
    parser.add_argument("-l",
                        "--wordLength",
                        help="number of syllables in the word(s)",
                        type=int,
                        default=0)
    parser.add_argument("-t",
                        "--type",
                        help="type of word to generate (noun|name|verb)",
                        type=str,
                        default="noun")
    parser.add_argument("-f",
                        "--format",
                        help="output format, must be text or json",
                        type=str,
                        default="text")
    args = parser.parse_args()

    wb = WordBuilder(args.ruletab)

    count = args.count
    length = args.wordLength  # ughck, where's my snake_case?
    mode = args.type

    wb.run(count, mode, length)

    if args.format == "json":
        print(json.dumps(sorted(wb.results)))
    else:
        for word in sorted(wb.results):
            print(word)