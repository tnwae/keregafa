import json

with open("keregafa_roots.tsv", "r") as fh:
    roots = {}
    lines = fh.readlines()

    for line in lines:
        root, meaning = line.split("\t")
        roots[root] = meaning.replace("\n", "")

    print(json.dumps(roots))
