import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "data" / "dictionary.db"


LANGUAGES = [
    ("de", "Deutsch", None, "Latin"),
    ("en", "Englisch", None, "Latin"),
    ("fr", "Französisch", None, "Latin"),
    ("it", "Italienisch", None, "Latin"),

    ("es", "Spanisch", None, "Latin"),
    ("es-MX", "Spanisch (Mexiko)", "Mexiko", "Latin"),

    ("pt-PT", "Portugiesisch (Portugal)", "Portugal", "Latin"),
    ("pt-BR", "Portugiesisch (Brasilien)", "Brasilien", "Latin"),

    ("fi", "Finnisch", None, "Latin"),
    ("nl", "Niederländisch", None, "Latin"),
    ("sv", "Schwedisch", None, "Latin"),
    ("no", "Norwegisch", None, "Latin"),
    ("da", "Dänisch", None, "Latin"),

    ("pl", "Polnisch", None, "Latin"),
    ("ro", "Rumänisch", None, "Latin"),
    ("sq", "Albanisch", None, "Latin"),
    ("bs", "Bosnisch", None, "Latin"),
    ("hr", "Kroatisch", None, "Latin"),
    ("sr", "Serbisch", None, "Cyrillic"),
    ("tr", "Türkisch", None, "Latin"),

    ("ru", "Russisch", None, "Cyrillic"),
    ("uk", "Ukrainisch", None, "Cyrillic"),
    ("el", "Griechisch", None, "Greek"),

    ("ar", "Arabisch", None, "Arabic"),
    ("fa", "Persisch / Farsi", None, "Arabic"),
    ("ur", "Urdu", None, "Arabic"),

    ("hi", "Hindi", None, "Devanagari"),
    ("bn", "Bengalisch", None, "Bengali"),
    ("ta", "Tamilisch", None, "Tamil"),

    ("ko", "Koreanisch", None, "Hangul"),
    ("ja", "Japanisch", None, "Japanese"),

    ("zh-Hans", "Chinesisch (vereinfacht)", "China", "Han"),
    ("zh-Hant", "Chinesisch (traditionell)", None, "Han"),

    ("vi", "Vietnamesisch", None, "Latin"),
    ("th", "Thai", None, "Thai"),
]


def get_connection():
    """
    Erstellt eine Verbindung zur SQLite-Datenbank.
    """

    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


def create_database():
    """
    Erstellt alle benötigten Tabellen und Indizes.

    Bereits vorhandene Daten werden NICHT gelöscht.
    """

    connection = get_connection()
    cursor = connection.cursor()

    # =========================================================
    # SPRACHEN
    # =========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS languages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            region TEXT,
            script TEXT
        )
    """)

    # =========================================================
    # WÖRTER
    # =========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            language_id INTEGER NOT NULL,
            word TEXT NOT NULL,
            word_type TEXT,

            FOREIGN KEY (language_id)
                REFERENCES languages(id)
                ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_word
        ON words(language_id, word)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_word_lookup
        ON words(word, language_id)
    """)

    # =========================================================
    # BISHERIGE ÜBERSETZUNGEN
    #
    # Diese Tabelle bleibt bestehen.
    # Dadurch funktioniert unsere aktuelle GUI weiterhin.
    # =========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS translations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            source_word_id INTEGER NOT NULL,
            target_word_id INTEGER NOT NULL,

            FOREIGN KEY (source_word_id)
                REFERENCES words(id)
                ON DELETE CASCADE,

            FOREIGN KEY (target_word_id)
                REFERENCES words(id)
                ON DELETE CASCADE,

            UNIQUE(
                source_word_id,
                target_word_id
            )
        )
    """)

    # Sehr wichtig für schnelle Übersetzungssuche.

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_translations_source
        ON translations(source_word_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_translations_target
        ON translations(target_word_id)
    """)

    # =========================================================
    # BEDEUTUNGEN / SENSES
    #
    # Beispiel:
    #
    # hallo
    #   Sense 1 -> Aufmerksamkeit
    #   Sense 2 -> Begrüssung
    #   Sense 3 -> Telefon
    # =========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meanings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            word_id INTEGER NOT NULL,

            sense_number TEXT,
            definition TEXT,
            part_of_speech TEXT,
            source_reference TEXT,

            FOREIGN KEY (word_id)
                REFERENCES words(id)
                ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_meanings_word
        ON meanings(word_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_meanings_source_reference
        ON meanings(source_reference)
    """)

    # =========================================================
    # ÜBERSETZUNGEN PRO BEDEUTUNG
    #
    # Beispiel:
    #
    # hallo
    #   Begrüssung
    #       -> hello
    #       -> hi
    #
    #   Telefon
    #       -> allô
    #       -> pronto
    # =========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meaning_translations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            meaning_id INTEGER NOT NULL,
            target_word_id INTEGER NOT NULL,

            FOREIGN KEY (meaning_id)
                REFERENCES meanings(id)
                ON DELETE CASCADE,

            FOREIGN KEY (target_word_id)
                REFERENCES words(id)
                ON DELETE CASCADE,

            UNIQUE(
                meaning_id,
                target_word_id
            )
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_meaning_translations_meaning
        ON meaning_translations(meaning_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_meaning_translations_target
        ON meaning_translations(target_word_id)
    """)

    connection.commit()
    connection.close()


def insert_languages():
    """
    Fügt die unterstützten Sprachen ein.

    Bereits vorhandene Sprachen werden
    nicht doppelt erstellt.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.executemany("""
        INSERT OR IGNORE INTO languages (
            code,
            name,
            region,
            script
        )
        VALUES (?, ?, ?, ?)
    """, LANGUAGES)

    connection.commit()

    cursor.execute("""
        SELECT code, name
        FROM languages
        ORDER BY name
    """)

    languages = cursor.fetchall()

    connection.close()

    return languages


def get_languages():
    """
    Gibt alle unterstützten Sprachen zurück.

    Wird von der GUI verwendet.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT code, name
        FROM languages
        ORDER BY name
    """)

    languages = cursor.fetchall()

    connection.close()

    return languages


def optimize_database():
    """
    Aktualisiert die SQLite-Statistiken.

    Das ist bei unserer grossen Wörterbuchdatenbank
    besonders wichtig, damit SQLite die richtigen
    Indizes verwendet.
    """

    connection = get_connection()

    connection.execute(
        "ANALYZE"
    )

    connection.execute(
        "PRAGMA optimize"
    )

    connection.commit()
    connection.close()


def get_database_statistics():
    """
    Liefert einige einfache Statistiken
    über die Wörterbuchdatenbank.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM languages
    """)

    language_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM words
    """)

    word_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM translations
    """)

    translation_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM meanings
    """)

    meaning_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM meaning_translations
    """)

    meaning_translation_count = cursor.fetchone()[0]

    connection.close()

    return {
        "languages": language_count,
        "words": word_count,
        "translations": translation_count,
        "meanings": meaning_count,
        "meaning_translations": meaning_translation_count,
    }


if __name__ == "__main__":

    print()
    print("Initialisiere Wörterbuchdatenbank...")
    print()

    create_database()

    languages = insert_languages()

    optimize_database()

    statistics = get_database_statistics()

    print(f"Datenbank: {DATABASE_PATH}")

    print()
    print("Installierte Sprachen:")
    print("----------------------")

    for code, name in languages:

        print(
            f"{code:10} {name}"
        )

    print()
    print("Datenbankstatistik:")
    print("----------------------")

    print(
        f"Sprachen:                 "
        f"{statistics['languages']:,}"
    )

    print(
        f"Wörter:                   "
        f"{statistics['words']:,}"
    )

    print(
        f"Übersetzungen:            "
        f"{statistics['translations']:,}"
    )

    print(
        f"Bedeutungen:              "
        f"{statistics['meanings']:,}"
    )

    print(
        f"Bedeutungsübersetzungen:  "
        f"{statistics['meaning_translations']:,}"
    )

    print()
    print(
        "SQLite-Indizes und Statistiken "
        "wurden aktualisiert."
    )