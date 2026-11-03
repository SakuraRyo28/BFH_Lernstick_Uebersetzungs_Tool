import re
import sys
from collections import Counter
from pathlib import Path


def analyze_languages(file_path):

    path = Path(file_path)

    if not path.exists():
        print(f"Datei nicht gefunden: {path}")
        return

    language_counter = Counter()

    print()
    print("Analysiere DBnary-Sprachen...")
    print(f"Datei: {path}")
    print()

    pattern = re.compile(
        r"dbnary:targetLanguage\s+lexvo:([a-z]{3})"
    )

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        for line_number, line in enumerate(
            file,
            start=1
        ):

            match = pattern.search(line)

            if match:
                language_counter[
                    match.group(1)
                ] += 1

            if line_number % 1_000_000 == 0:
                print(
                    f"\rZeilen analysiert: "
                    f"{line_number:,}",
                    end="",
                    flush=True
                )

    print()
    print()
    print("Gefundene Zielsprachen")
    print("=" * 50)

    for code, count in language_counter.most_common():

        print(
            f"{code:10} {count:>10,}"
        )

    print()
    print("=" * 50)

    print(
        f"Unterschiedliche Sprachcodes: "
        f"{len(language_counter)}"
    )

    print(
        f"Übersetzungsangaben insgesamt: "
        f"{sum(language_counter.values()):,}"
    )


if __name__ == "__main__":

    if len(sys.argv) < 2:

        print(
            "python -m scripts.analyze_dbnary_languages "
            "data/de_dbnary_ontolex.ttl"
        )

        sys.exit(1)

    analyze_languages(
        sys.argv[1]
    )