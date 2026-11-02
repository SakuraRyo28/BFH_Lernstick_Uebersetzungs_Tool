import json
import sys
from pathlib import Path

from database.database import get_connection


def get_language_id(cursor, language_code):
    """
    Sucht die ID einer Sprache anhand ihres Sprachcodes.
    Beispiel:
    de -> ID von Deutsch
    ko -> ID von Koreanisch
    """

    cursor.execute(
        """
        SELECT id
        FROM languages
        WHERE code = ?
        """,
        (language_code,)
    )

    result = cursor.fetchone()

    if result:
        return result[0]

    return None


def get_or_create_word(cursor, language_id, word, word_type=None):
    """
    Prüft, ob ein Wort bereits existiert.

    Falls ja:
        bestehende ID zurückgeben.

    Falls nein:
        Wort erstellen und neue ID zurückgeben.
    """

    cursor.execute(
        """
        SELECT id
        FROM words
        WHERE language_id = ?
        AND word = ?
        """,
        (language_id, word)
    )

    result = cursor.fetchone()

    if result:
        return result[0]

    cursor.execute(
        """
        INSERT INTO words (
            language_id,
            word,
            word_type
        )
        VALUES (?, ?, ?)
        """,
        (
            language_id,
            word,
            word_type
        )
    )

    return cursor.lastrowid


def create_translation(cursor, source_word_id, target_word_id):
    """
    Erstellt eine Übersetzungsverbindung zwischen zwei Wörtern.

    INSERT OR IGNORE verhindert doppelte Verbindungen.
    """

    if source_word_id == target_word_id:
        return False

    cursor.execute(
        """
        INSERT OR IGNORE INTO translations (
            source_word_id,
            target_word_id
        )
        VALUES (?, ?)
        """,
        (
            source_word_id,
            target_word_id
        )
    )

    return cursor.rowcount > 0


def import_dictionary(file_path):
    """
    Importiert Wörter und deren Übersetzungen
    aus einer JSONL-Datei.
    """

    file_path = Path(file_path)

    if not file_path.exists():
        print(f"Datei nicht gefunden: {file_path}")
        return

    connection = get_connection()
    cursor = connection.cursor()

    processed_entries = 0
    created_translations = 0
    skipped = 0

    print()
    print("Starte Wörterbuch-Import...")
    print(f"Datei: {file_path}")
    print()

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            for line_number, line in enumerate(file, start=1):

                line = line.strip()

                if not line:
                    continue

                try:
                    entry = json.loads(line)

                except json.JSONDecodeError:
                    skipped += 1
                    continue

                # Ausgangswort lesen

                source_word = entry.get("word")
                source_language_code = entry.get("lang_code")
                word_type = entry.get("pos")

                if not source_word or not source_language_code:
                    skipped += 1
                    continue

                # Sprache des Ausgangswortes suchen

                source_language_id = get_language_id(
                    cursor,
                    source_language_code
                )

                # Sprache wurde in unserer languages-Tabelle
                # noch nicht definiert

                if source_language_id is None:
                    skipped += 1
                    continue

                # Ausgangswort holen oder erstellen

                source_word_id = get_or_create_word(
                    cursor,
                    source_language_id,
                    source_word,
                    word_type
                )

                processed_entries += 1

                # Übersetzungen aus dem Eintrag lesen

                translations = entry.get(
                    "translations",
                    []
                )

                for translation in translations:

                    target_word = translation.get("word")

                    target_language_code = (
                        translation.get("code")
                        or translation.get("lang_code")
                    )

                    if not target_word:
                        continue

                    if not target_language_code:
                        continue

                    # Sprache der Übersetzung suchen

                    target_language_id = get_language_id(
                        cursor,
                        target_language_code
                    )

                    # Unbekannte Sprachen ignorieren

                    if target_language_id is None:
                        continue

                    # Zielwort erstellen oder vorhandenes verwenden

                    target_word_id = get_or_create_word(
                        cursor,
                        target_language_id,
                        target_word
                    )

                    # Quelle -> Ziel

                    created = create_translation(
                        cursor,
                        source_word_id,
                        target_word_id
                    )

                    if created:
                        created_translations += 1

                    # Ziel -> Quelle
                    #
                    # Dadurch funktioniert z. B.
                    # Deutsch -> Koreanisch
                    # UND
                    # Koreanisch -> Deutsch

                    create_translation(
                        cursor,
                        target_word_id,
                        source_word_id
                    )

                # Bei großen Wörterbüchern regelmäßig speichern

                if line_number % 1000 == 0:

                    connection.commit()

                    print(
                        f"\rVerarbeitet: {line_number:,}",
                        end="",
                        flush=True
                    )

        connection.commit()

    except Exception as error:

        connection.rollback()

        print()
        print("Fehler beim Import:")
        print(error)

        raise

    finally:

        connection.close()

    print()
    print()
    print("Import abgeschlossen")
    print("------------------------------")
    print(f"Einträge verarbeitet:     {processed_entries:,}")
    print(f"Übersetzungen erstellt:   {created_translations:,}")
    print(f"Übersprungen:             {skipped:,}")


if __name__ == "__main__":

    if len(sys.argv) < 2:

        print()
        print("Keine Importdatei angegeben.")
        print()
        print("Beispiel:")
        print(
            "python -m scripts.import_dictionary "
            "data/test_import.jsonl"
        )

        sys.exit(1)

    import_dictionary(
        sys.argv[1]
    )