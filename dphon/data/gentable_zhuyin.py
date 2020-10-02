"""Script to convert the Zhuyin sound table to JSON."""

import json
from collections import defaultdict


def run() -> None:
    """Parse a tab-delimited text file into a JSON object."""
    with open("dphon/data/sound_table_zhuyin.txt", encoding="utf8") as infile:
        entries = infile.readlines()

    output = defaultdict(str)

    for entry in entries:
        try:
            zhuyin, graphs = [p.strip() for p in entry.split("\t")[:2]]
            if graphs != "-":
                for graph in graphs:
                    output[graph] = zhuyin
        except ValueError:
            continue

    with open("dphon/data/sound_table_zhuyin.json", mode="w", encoding="utf8") as outfile:
        json.dump(output, outfile, ensure_ascii=False)

if __name__ == "__main__":
    run()
