import json

with open("prefixes.txt", "r") as fh:
    rules = {}
    for line in fh.readlines():
        mood, prefix, elide = line[:-1].split("\t")
        rules[mood.lower()] = {"prefix": prefix, "elide": elide}

    print(json.dumps(rules))
