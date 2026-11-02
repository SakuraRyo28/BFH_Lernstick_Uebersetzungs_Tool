from database.database import get_connection


def translate_word(
    word,
    source_language,
    target_language
):

    if not word:
        return []

    word = word.strip()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT DISTINCT target.word

        FROM words AS source

        JOIN languages AS source_language
            ON source.language_id =
               source_language.id

        JOIN translations
            ON source.id =
               translations.source_word_id

        JOIN words AS target
            ON translations.target_word_id =
               target.id

        JOIN languages AS target_language
            ON target.language_id =
               target_language.id

        WHERE LOWER(source.word) = LOWER(?)
          AND source_language.code = ?
          AND target_language.code = ?

        ORDER BY target.word
        """,
        (
            word,
            source_language,
            target_language
        )
    )

    results = cursor.fetchall()

    connection.close()

    return [
        row[0]
        for row in results
    ]