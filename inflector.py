#!/usr/bin/env python3

import conlang_utils as cu
import json
import sys
from typing import Tuple, List

noun_templates = dict()
noun_inflection_rules = dict()
mood_templates = dict()
tense_templates = dict()
converb_templates = dict()
tunings = None
conlang_data = None


def init_program(ruletab: str, data: str) -> None:
    global noun_templates
    global noun_inflection_rules
    global mood_templates
    global tense_templates
    global converb_templates
    global tunings
    global conlang_data

    conlang_data = cu.ConlangData(data)

    try:
        with open(ruletab, "r") as fp:
            raw = json.load(fp)
            noun_templates = raw["declensionTable"]
            noun_inflection_rules = raw["declensionInflectionRules"]
            tense_templates = raw["conjugationTable"]
            mood_templates = raw["verbPrefixTable"]
            converb_templates = raw["converbTable"]
            tunings = raw.get("tunings", None)
    except FileNotFoundError as ex:
        print(ex)
        sys.exit(1)


def inflect_noun(word: str) -> dict:
    action_tab = {
        "deleteLastChar": conlang_data.delete_last_char,
        "appendLastVowel": conlang_data.append_last_vowel,
        "appendLastConsonant": conlang_data.append_last_consonant,
        "doNothing": conlang_data.do_nothing_for_inflection
    }

    inflections = dict()
    word_tokens = conlang_data.tokenize_word(word)

    for kase, inflection in noun_templates.items():
        # get class of final token and initial char of case ending
        if inflection != "@":
            inflection_tokens = conlang_data.tokenize_word(inflection)

            final_token_class = conlang_data.get_char_class(word_tokens[-1])
            case_ending_class = conlang_data.get_char_class(
                inflection_tokens[0])

            # the rule table is keyed on the class of the final token of the word,
            # combined with the class of the first token of the inflection.
            rule = noun_inflection_rules[final_token_class][case_ending_class]
            inflections[kase] = conlang_data.detokenize_word(
                action_tab[rule](word_tokens) + inflection_tokens)
        else:
            inflections[kase] = conlang_data.detokenize_word(word_tokens)

    return inflections


def inflect_verb(word: str) -> dict:
    root, ending = word[:-2], word[-2:]
    tense_rules = tense_templates[ending]
    inflection = {"tenses": {}, "moods": {}, "converbs": {}}

    if tunings:
        converb_root_form = tunings.get("applyConverbToVerbForm", None)

    for tense, tense_ending in tense_rules.items():
        inflection["tenses"][tense] = root + tense_ending

    for mood, mood_rule in mood_templates.items():
        if mood_rule["prefix"] == "@":
            inflection["moods"][mood] = word
        else:
            prefix = mood_rule["prefix"]
            elide = mood_rule["elide"]
            if conlang_data.get_char_class(
                    prefix[-1]) == conlang_data.get_char_class(word[0]):
                inflection["moods"][mood] = prefix + elide + word
            else:
                inflection["moods"][mood] = prefix + word

    converb_candidates = inflect_noun(inflection["tenses"][converb_root_form])
    for type, kase in converb_templates.items():
        inflection["converbs"][type] = converb_candidates[kase]

    return inflection


if __name__ == "__main__":
    import argparse

    inflectors = {"v": inflect_verb, "n": inflect_noun}

    parser = argparse.ArgumentParser("inflector")
    parser.add_argument("-r",
                        "--ruletab",
                        help="rule table file (default: keregafa_rules.json)",
                        type=str,
                        default="./keregafa_rules.json")
    parser.add_argument("-l",
                        "--languagedata",
                        help="language data file (default: keregafa.json)",
                        type=str,
                        default="./keregafa.json")
    parser.add_argument("word", help="word to inflect", type=str)
    parser.add_argument("-t",
                        "--type",
                        help="type of inflection to perform",
                        type=str,
                        default="n")
    args = parser.parse_args()

    init_program(args.ruletab, args.languagedata)

    inflector = inflectors[args.type]
    inflected_word = inflector(args.word)

    print(json.dumps(inflected_word, indent=4))
