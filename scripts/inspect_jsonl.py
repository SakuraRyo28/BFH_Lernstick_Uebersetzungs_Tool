import json
import sys
from pathlib import Path


def inspect_jsonl(file_path, limit=10):

    path = Path(file_path)

    if not path.exists():
        print(f"Datei nicht gefunden: {path}")
        return

    print()
    print(f"Analysiere: {path}")
    print("=" * 70)

    count = 0
    entries_with_translations = 0

    with open(path, "r", encoding="utf-8") as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            try:
                entry = json.loads(line)

            except json.JSONDecodeError:
                continue

            word = entry.get("word")
            lang_code = entry.get("lang_code")
            pos = entry.get("pos")

            senses = entry.get("senses", [])

            # Übersetzungen können theoretisch
            # auf verschiedenen Ebenen vorkommen.
            top_translations = entry.get("translations", [])

            sense_translations = []

            for sense in senses:
                translations = sense.get("translations", [])

                if translations:
                    sense_translations.extend(translations)

            all_translations = (
                top_translations
                + sense_translations
            )

            # Wir interessieren uns besonders
            # für Einträge mit Übersetzungen.
            if not all_translations:
                continue

            entries_with_translations += 1
            count += 1

            print()
            print(f"EINTRAG MIT ÜBERSETZUNGEN {count}")
            print("-" * 70)

            print(f"Wort:        {word}")
            print(f"Sprache:     {lang_code}")
            print(f"Wortart:     {pos}")
            print(f"Senses:      {len(senses)}")
            print(f"Übersetzungen: {len(all_translations)}")

            print()
            print("Vorhandene Felder:")
            print(", ".join(entry.keys()))

            print()
            print("ÜBERSETZUNGEN")
            print("-" * 70)

            for translation in all_translations[:20]:

                print(
                    "Wort:",
                    translation.get("word"),
                    "| code:",
                    translation.get("code"),
                    "| lang_code:",
                    translation.get("lang_code"),
                    "| lang:",
                    translation.get("lang")
                )

            print()
            print("ERSTES SENSE-OBJEKT")
            print("-" * 70)

            if senses:
                print(
                    json.dumps(
                        senses[0],
                        ensure_ascii=False,
                        indent=2
                    )
                )

            print("=" * 70)

            if count >= limit:
                break

    print()
    print("Analyse beendet.")

    if entries_with_translations == 0:
        print()
        print(
            "Keine Übersetzungen wurden in den "
            "untersuchten Einträgen gefunden."
        )


if __name__ == "__main__":

    if len(sys.argv) < 2:

        print()
        print("Benutzung:")
        print(
            "python -m scripts.inspect_jsonl "
            "DATEI.jsonl"
        )

        sys.exit(1)

    inspect_jsonl(
        sys.argv[1]
    )