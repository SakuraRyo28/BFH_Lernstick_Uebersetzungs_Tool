from database.database import get_connection


WORDS = [
    # Begriff, Sprachcode, Wort
    ("house", "de", "Haus"),
    ("house", "en", "house"),
    ("house", "fr", "maison"),
    ("house", "it", "casa"),
    ("house", "es", "casa"),
    ("house", "es-MX", "casa"),
    ("house", "pt-BR", "casa"),
    ("house", "fi", "talo"),
    ("house", "ru", "дом"),
    ("house", "ko", "집"),
    ("house", "zh-Hans", "房子"),
    ("house", "ta", "வீடு"),

    ("school", "de", "Schule"),
    ("school", "en", "school"),
    ("school", "fr", "école"),
    ("school", "it", "scuola"),
    ("school", "es", "escuela"),
    ("school", "pt-BR", "escola"),
    ("school", "fi", "koulu"),
    ("school", "ru", "школа"),
    ("school", "ko", "학교"),
    ("school", "zh-Hans", "学校"),
    ("school", "ta", "பள்ளி"),
]


def seed_words():
    connection = get_connection()
    cursor = connection.cursor()

    concept_words = {}

    for concept, language_code, word in WORDS:

        cursor.execute(
            "SELECT id FROM languages WHERE code = ?",
            (language_code,)
        )

        language = cursor.fetchone()

        if not language:
            print(f"Sprache nicht gefunden: {language_code}")
            continue

        language_id = language[0]

        cursor.execute(
            """
            SELECT id FROM words
            WHERE language_id = ? AND word = ?
            """,
            (language_id, word)
        )

        existing_word = cursor.fetchone()

        if existing_word:
            word_id = existing_word[0]
        else:
            cursor.execute(
                """
                INSERT INTO words (language_id, word)
                VALUES (?, ?)
                """,
                (language_id, word)
            )

            word_id = cursor.lastrowid

        concept_words.setdefault(concept, []).append(word_id)

    # Alle Wörter desselben Begriffs miteinander verbinden
    for word_ids in concept_words.values():

        for source_id in word_ids:
            for target_id in word_ids:

                if source_id == target_id:
                    continue

                cursor.execute(
                    """
                    INSERT OR IGNORE INTO translations
                    (source_word_id, target_word_id)
                    VALUES (?, ?)
                    """,
                    (source_id, target_id)
                )

    connection.commit()
    connection.close()

    print("Testwörter wurden erfolgreich eingefügt.")


if __name__ == "__main__":
    seed_words()
