import sys
from pathlib import Path


def inspect_dbnary(file_path, limit=100):

    path = Path(file_path)

    if not path.exists():
        print(f"Datei nicht gefunden: {path}")
        return

    print()
    print("DBnary-Datei wird analysiert")
    print("=" * 70)
    print(f"Datei: {path}")
    print()

    file_size = path.stat().st_size

    print(
        f"Dateigrösse: "
        f"{file_size / 1024 / 1024:.2f} MB"
    )

    print()
    print("Erste Turtle-Zeilen")
    print("=" * 70)

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            count = 0

            for line_number, line in enumerate(
                file,
                start=1
            ):

                line = line.rstrip()

                if not line:
                    continue

                print(
                    f"{line_number:6}: {line}"
                )

                count += 1

                if count >= limit:
                    break

    except Exception as error:

        print()
        print("Fehler beim Lesen:")
        print(error)
        return

    print()
    print("=" * 70)
    print("Analyse beendet.")


if __name__ == "__main__":

    if len(sys.argv) < 2:

        print()
        print("Benutzung:")
        print(
            "python -m scripts.inspect_dbnary "
            "DATEI.ttl"
        )

        sys.exit(1)

    inspect_dbnary(
        sys.argv[1]
    )