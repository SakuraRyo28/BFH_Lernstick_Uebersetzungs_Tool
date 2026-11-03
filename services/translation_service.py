from database.database import get_connection


def translate_word(
    word,
    source_language,
    target_language
):
    """
    Einfache Übersetzung ohne Bedeutungsgruppierung.

    Diese Funktion bleibt bestehen,
    damit ältere Teile der Anwendung
    weiterhin funktionieren.
    """

    if not word:
        return []

    word = word.strip()

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT DISTINCT target.word

            FROM languages AS source_language

            JOIN words AS source
                ON source.language_id = source_language.id

            JOIN translations
                ON translations.source_word_id = source.id

            JOIN words AS target
                ON target.id = translations.target_word_id

            JOIN languages AS target_language
                ON target.language_id = target_language.id

            WHERE source_language.code = ?
              AND source.word = ?
              AND target_language.code = ?

            ORDER BY target.word
            """,
            (
                source_language,
                word,
                target_language
            )
        )

        results = cursor.fetchall()

        return [
            row[0]
            for row in results
        ]

    finally:

        connection.close()


def translate_word_with_meanings(
    word,
    source_language,
    target_language
):
    """
    Übersetzt ein Wort und gruppiert die Ergebnisse
    nach Bedeutung / Sense.

    Rückgabe:

    [
        {
            "sense_number": "2",
            "definition": "...",
            "part_of_speech": "Interjektion",
            "translations": ["hello", "hi"]
        }
    ]
    """

    if not word:
        return []

    word = word.strip()

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                m.id,
                m.sense_number,
                m.definition,
                m.part_of_speech,
                target.word

            FROM languages AS source_language

            JOIN words AS source
                ON source.language_id = source_language.id

            JOIN meanings AS m
                ON m.word_id = source.id

            JOIN meaning_translations AS mt
                ON mt.meaning_id = m.id

            JOIN words AS target
                ON target.id = mt.target_word_id

            JOIN languages AS target_language
                ON target_language.id = target.language_id

            WHERE source_language.code = ?
              AND source.word = ?
              AND target_language.code = ?

            ORDER BY
                CASE
                    WHEN m.sense_number GLOB '[0-9]*'
                    THEN CAST(m.sense_number AS INTEGER)
                    ELSE 999999
                END,
                m.sense_number,
                target.word
            """,
            (
                source_language,
                word,
                target_language
            )
        )

        rows = cursor.fetchall()

        meanings = {}

        for (
            meaning_id,
            sense_number,
            definition,
            part_of_speech,
            translation
        ) in rows:

            if meaning_id not in meanings:

                meanings[meaning_id] = {
                    "sense_number": sense_number,
                    "definition": definition,
                    "part_of_speech": part_of_speech,
                    "translations": []
                }

            if (
                translation
                not in meanings[meaning_id][
                    "translations"
                ]
            ):

                meanings[meaning_id][
                    "translations"
                ].append(
                    translation
                )

        return list(
            meanings.values()
        )

    finally:

        connection.close()


def translate(
    word,
    source_language,
    target_language
):
    """
    Hauptfunktion der Anwendung.

    Versucht zuerst die neue
    bedeutungsbasierte Übersetzung.

    Falls für ein Wort noch keine
    Bedeutungsdaten existieren,
    verwenden wir die ältere
    Übersetzungstabelle als Fallback.
    """

    meanings = translate_word_with_meanings(
        word,
        source_language,
        target_language
    )

    if meanings:

        return {
            "type": "meanings",
            "results": meanings
        }

    translations = translate_word(
        word,
        source_language,
        target_language
    )

    return {
        "type": "simple",
        "results": translations
    }