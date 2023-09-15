#!/usr/bin/env python3

import sys
import json
from random import random
from typing import List, Union
import numpy as np

## todo: write some unit tests


class ConlangData:
    consonant_freqtab = dict()
    vowel_freqtab = dict()
    phoneme_classes = dict()
    voicing_rules = dict()
    word_types = dict()
    syllable_types = dict()
    replacement_rules = dict()
    harmony_rules = dict()
    sigil_encode_table = dict()
    sigil_decode_table = dict()

    def __init__(self, ruletab_fn: str) -> None:
        char_offset = 0x4E00
        try:
            with open(ruletab_fn) as fp:
                raw = json.load(fp)
                self.consonant_freqtab = raw["consonantFrequencies"]
                self.vowel_freqtab = raw["vowelFrequencies"]
                self.phoneme_classes = raw["phonemeClasses"]
                self.word_types = raw["wordTypes"]
                self.syllable_types = raw["syllableClasses"]
                self.voicing_rules = raw.get("voicingRules", None)
                self.replacement_rules = raw.get("replacementRules", None)
                self.harmony_rules = raw.get("harmonyRules", None)
                self.tunings = raw.get("tuning", None)
        except Exception as ex:
            print(ex)
            sys.exit(1)

        consonants = [l for l in self.consonant_freqtab.keys()]
        vowels = [l for l in self.vowel_freqtab.keys()]
        phonemes = vowels + consonants
        for phoneme in phonemes:
            sigil = chr(char_offset)
            self.sigil_encode_table[phoneme] = sigil
            self.sigil_decode_table[sigil] = phoneme

            char_offset += 1

    def harmonize(self, word: List[str], nucleus_vowel: str) -> List[str]:
        nucleus_vowel_class = None
        if not self.harmony_rules or not nucleus_vowel:
            return word
        else:
            harmonized_word = word
            for klass, vowels in self.harmony_rules["vowelClasses"].items():
                if nucleus_vowel in vowels:
                    nucleus_vowel_class = klass

            if not nucleus_vowel_class:
                raise Exception(
                    f"nucleus vowel {nucleus_vowel} not in any vowel class (potential classes are [{self.harmony_rules['vowelClasses'].keys()}])"
                )
            counterparts = self.harmony_rules["counterparts"][
                nucleus_vowel_class]
            for i in range(len(word)):
                ch = word[i]
                subst = counterparts.get(ch, ch)
                harmonized_word[i] = subst
            return harmonized_word

    def get_char(self, phoneme_class: str, vowelp: bool = False) -> str:
        if phoneme_class.isupper():
            phonemes_in_class = self.phoneme_classes[phoneme_class]
            freqtab = self.vowel_freqtab if vowelp else self.consonant_freqtab
            ch = ""

            while ch not in phonemes_in_class:
                ch = np.random.choice(list(freqtab.keys()),
                                      1,
                                      p=list(freqtab.values()))

            retval = ch[0]

            geminate_values = self.geminate() if not vowelp else None
            if geminate_values and geminate_values["geminate"]:
                if not geminate_values["geminatableConsonants"] or \
                       ch[0] in geminate_values["geminatableConsonants"]:
                    retval = ch[0] * 2

            return retval
        else:
            return phoneme_class

    def geminate(self) -> Union[dict, None]:
        retval = dict()
        if self.tunings:
            chance = self.tunings.get("geminateConsonantChance", None)
            if chance:
                retval["geminate"] = (chance > random())
                retval["geminatableConsonants"] = self.tunings.get(
                    "geminatableConsonants", None)
                return retval

        return None

    def reduplicate(self) -> Union[dict, None]:
        retval = dict()
        if self.tunings:
            chance = self.tunings.get("reduplicateChance", None)
            if chance:
                retval["reduplicate"] = (chance > random())
                retval["initialVoice"] = self.tunings.get(
                    "reduplicateWithInitialVoicing", False)
                return retval

        return None

    def reduplicate_word(self, word: list) -> Union[list, None]:
        reduplicate_values = self.reduplicate()

        if reduplicate_values and reduplicate_values["reduplicate"] \
                              and len(word) < 6:
            reduplicated = [ch for ch in word]

            # de/voice the initial consonant (e.g. todu -> dodu)
            reduplicated[0] = self.voicing_rules.get(reduplicated[0],
                                                     reduplicated[0])
            reduplicated.extend(reduplicated)

            # reverse the de/voicing on the first half of the reduplicated stem
            # (e.g. dodudodu -> todudodu)
            reduplicated[0] = self.voicing_rules.get(reduplicated[0],
                                                     reduplicated[0])
            return reduplicated

        return None

    def is_vowel(self, ch: str) -> bool:
        return ch in self.phoneme_classes["V"]

    def compile_syllable_class(self, ch: str) -> str:
        if ch in self.syllable_types.keys():
            return np.random.choice(self.syllable_types[ch])
        else:
            raise Exception(ch)

    def compile_char(self, ch: str) -> str:
        if ch in "V":
            vowelp = True
        else:
            vowelp = False
        return self.get_char(ch, vowelp)

    def tokenize_word(self, word: str) -> List[str]:
        encoded_word = word

        for phoneme, sigil in dict(
                sorted(self.sigil_encode_table.items(),
                       key=(lambda i: len(i[0])),
                       reverse=True)).items():
            encoded_word = encoded_word.replace(phoneme, sigil)

        return [self.sigil_decode_table[ch] for ch in encoded_word]

    def detokenize_word(self, word: List[str]) -> str:
        return "".join(word)

    def _find_consonants(self, word: List[str]) -> List[str]:
        return [ch for ch in word if not self.is_vowel(ch)]

    def _find_vowels(self, word: List[str]) -> List[str]:
        return [ch for ch in word if self.is_vowel(ch)]

    def _give_last_consonant(self, word: List[str]) -> List[str]:
        return [self._find_consonants(word)[-1]]

    def _give_last_vowel(self, word: List[str]) -> List[str]:
        return [self._find_vowels(word)[-1]]

    def append_last_consonant(self, word: List[str]) -> str:
        return word + self._give_last_consonant(word)

    def append_last_vowel(self, word: List[str]) -> str:
        return word + self._give_last_vowel(word)

    def delete_last_char(self, word: List[str]) -> List[str]:
        return word[:-1]

    def do_nothing_for_inflection(self, word: List[str]) -> List[str]:
        return word

    def get_char_class(self, ch: str) -> str:
        for klass, members in self.phoneme_classes.items():
            if ch in members:
                return klass
        else:
            raise Exception("invalid character")
