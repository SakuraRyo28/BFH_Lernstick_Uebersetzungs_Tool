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
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def create_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS languages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            region TEXT,
            script TEXT
        )
    """)

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

            UNIQUE(source_word_id, target_word_id)
        )
    """)

    connection.commit()
    connection.close()


def insert_languages():
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

if __name__ == "__main__":
    create_database()

    languages = insert_languages()

    print(f"Datenbank: {DATABASE_PATH}")
    print()
    print("Installierte Sprachen:")
    print("----------------------")

    for code, name in languages:
        print(f"{code:10} {name}")

    print()
    print(f"Anzahl Sprachen: {len(languages)}")