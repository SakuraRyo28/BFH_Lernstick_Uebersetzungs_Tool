import re
import sys
from pathlib import Path

from database.database import get_connection


# ============================================================
# DBNARY ISO-639-3 -> UNSERE SPRACHCODES
# ============================================================

LANGUAGE_MAP = {
    "deu": "de",
    "eng": "en",
    "fra": "fr",
    "ita": "it",

    "spa": "es",
    "por": "pt-PT",

    "fin": "fi",
    "nld": "nl",
    "swe": "sv",
    "nor": "no",
    "dan": "da",

    "pol": "pl",
    "ron": "ro",
    "sqi": "sq",
    "bos": "bs",
    "hrv": "hr",
    "srp": "sr",
    "tur": "tr",

    "rus": "ru",
    "ukr": "uk",
    "ell": "el",

    "ara": "ar",
    "fas": "fa",
    "urd": "ur",

    "hin": "hi",
    "ben": "bn",
    "tam": "ta",

    "kor": "ko",
    "jpn": "ja",

    "zho": "zh-Hans",

    "vie": "vi",
    "tha": "th",
}


# ============================================================
# HILFSFUNKTIONEN
# ============================================================

def get_language_id(cursor, language_code):

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


def get_or_create_word(
    cursor,
    language_id,
    word,
    word_type=None
):

    cursor.execute(
        """
        SELECT id
        FROM words
        WHERE language_id = ?
          AND word = ?
        """,
        (
            language_id,
            word
        )
    )

    result = cursor.fetchone()

    if result:

        word_id = result[0]

        # Falls bisher noch keine Wortart gespeichert wurde,
        # können wir sie ergänzen.

        if word_type:

            cursor.execute(
                """
                UPDATE words
                SET word_type = COALESCE(word_type, ?)
                WHERE id = ?
                """,
                (
                    word_type,
                    word_id
                )
            )

        return word_id

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


def create_translation(
    cursor,
    source_word_id,
    target_word_id
):

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


def get_or_create_meaning(
    cursor,
    word_id,
    sense_number,
    definition,
    part_of_speech,
    source_reference
):

    # DBnary source_reference ist für uns
    # die stabilste Identifikation eines Senses.

    if source_reference:

        cursor.execute(
            """
            SELECT id
            FROM meanings
            WHERE source_reference = ?
            LIMIT 1
            """,
            (source_reference,)
        )

        result = cursor.fetchone()

        if result:
            return result[0]

    cursor.execute(
        """
        SELECT id
        FROM meanings
        WHERE word_id = ?
          AND COALESCE(sense_number, '') =
              COALESCE(?, '')
          AND COALESCE(definition, '') =
              COALESCE(?, '')
        LIMIT 1
        """,
        (
            word_id,
            sense_number,
            definition
        )
    )

    result = cursor.fetchone()

    if result:
        return result[0]

    cursor.execute(
        """
        INSERT INTO meanings (
            word_id,
            sense_number,
            definition,
            part_of_speech,
            source_reference
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            word_id,
            sense_number,
            definition,
            part_of_speech,
            source_reference
        )
    )

    return cursor.lastrowid


def create_meaning_translation(
    cursor,
    meaning_id,
    target_word_id
):

    cursor.execute(
        """
        INSERT OR IGNORE INTO meaning_translations (
            meaning_id,
            target_word_id
        )
        VALUES (?, ?)
        """,
        (
            meaning_id,
            target_word_id
        )
    )

    return cursor.rowcount > 0


def clean_turtle_string(value):

    if value is None:
        return None

    value = value.strip()

    value = value.replace('\\"', '"')
    value = value.replace("\\\\", "\\")

    return value


# ============================================================
# HAUPTIMPORT
# ============================================================

def import_dbnary(file_path):

    path = Path(file_path)

    if not path.exists():

        print(
            f"Datei nicht gefunden: {path}"
        )

        return

    print()
    print("DBnary Import mit Bedeutungen")
    print("=" * 65)
    print(f"Datei: {path}")
    print()

    connection = get_connection()
    cursor = connection.cursor()

    german_language_id = get_language_id(
        cursor,
        "de"
    )

    if german_language_id is None:

        connection.close()

        print(
            "Deutsch ist nicht in der "
            "languages-Tabelle vorhanden."
        )

        return

    # ========================================================
    # CACHE / ZUORDNUNGEN
    # ========================================================

    # LexicalEntry -> Informationen
    #
    # Beispiel:
    #
    # deu:hallo__Interjektion__1
    # ->
    # {
    #   word: "hallo",
    #   word_id: 123,
    #   part_of_speech: "Interjektion"
    # }

    lexical_entries = {}

    # Sense-Ressource -> LexicalEntry
    #
    # Beispiel:
    #
    # deu:__ws_2_hallo__Interjektion__1
    # ->
    # deu:hallo__Interjektion__1

    sense_to_entry = {}

    # Sense-Ressource -> Datenbank meaning_id

    sense_to_meaning = {}

    # (LexicalEntry, SenseNumber) -> meaning_id

    entry_sense_to_meaning = {}

    # Gloss-Ressource -> SenseNumber
    #
    # Übersetzungen verweisen auf Gloss-Ressourcen.

    gloss_to_sense_number = {}

    # ========================================================
    # STATISTIK
    # ========================================================

    processed_blocks = 0

    created_meanings = 0
    created_meaning_translations = 0

    created_legacy_translations = 0

    skipped_languages = 0
    translations_without_meaning = 0

    # ========================================================
    # BLOCK VERARBEITEN
    # ========================================================

    def process_block(subject, lines):

        nonlocal created_meanings
        nonlocal created_meaning_translations
        nonlocal created_legacy_translations
        nonlocal skipped_languages
        nonlocal translations_without_meaning

        if not subject:
            return

        text = " ".join(lines)

        # ====================================================
        # 1. LEXICAL ENTRY
        # ====================================================

        if "ontolex:LexicalEntry" in text:

            label_match = re.search(
                r'rdfs:label\s+"((?:[^"\\]|\\.)*)"@de',
                text
            )

            if not label_match:
                return

            word = clean_turtle_string(
                label_match.group(1)
            )

            pos_match = re.search(
                r'dbnary:partOfSpeech\s+"((?:[^"\\]|\\.)*)"',
                text
            )

            part_of_speech = None

            if pos_match:

                part_of_speech = clean_turtle_string(
                    pos_match.group(1)
                )

            word_id = get_or_create_word(
                cursor,
                german_language_id,
                word,
                part_of_speech
            )

            lexical_entries[subject] = {
                "word": word,
                "word_id": word_id,
                "part_of_speech": part_of_speech
            }

            # Alle ontolex:sense-Ressourcen sammeln.
            #
            # Beispiel:
            #
            # ontolex:sense
            #     deu:__ws_1_...
            #     deu:__ws_2_...
            #     deu:__ws_3_...

            sense_section_match = re.search(
                r'ontolex:sense\s+([^.]*)\.',
                text
            )

            if sense_section_match:

                sense_section = (
                    sense_section_match.group(1)
                )

                senses = re.findall(
                    r'deu:__[^\s,;]+',
                    sense_section
                )

                for sense_resource in senses:

                    sense_to_entry[
                        sense_resource
                    ] = subject

            return

        # ====================================================
        # 2. LEXICAL SENSE
        # ====================================================

        if "ontolex:LexicalSense" in text:

            sense_number_match = re.search(
                r'dbnary:senseNumber\s+"([^"]+)"',
                text
            )

            sense_number = None

            if sense_number_match:

                sense_number = (
                    sense_number_match.group(1)
                )

            # Definition lesen.
            #
            # Beispiel:
            #
            # skos:definition
            # [ rdf:value "Grußwort ..."@de ]

            definition_match = re.search(
                r'skos:definition\s+\[\s*'
                r'rdf:value\s+'
                r'"((?:[^"\\]|\\.)*)"@de',
                text
            )

            definition = None

            if definition_match:

                definition = clean_turtle_string(
                    definition_match.group(1)
                )

            entry_resource = sense_to_entry.get(
                subject
            )

            if not entry_resource:
                return

            entry = lexical_entries.get(
                entry_resource
            )

            if not entry:
                return

            meaning_id = get_or_create_meaning(
                cursor,
                entry["word_id"],
                sense_number,
                definition,
                entry["part_of_speech"],
                subject
            )

            sense_to_meaning[
                subject
            ] = meaning_id

            if sense_number:

                entry_sense_to_meaning[
                    (
                        entry_resource,
                        sense_number
                    )
                ] = meaning_id

            created_meanings += 1

            return

        # ====================================================
        # 3. GLOSS
        # ====================================================
        #
        # Beispiel:
        #
        # deu:__de_gloss_VZv3QQ--_hallo...
        #   rdf:type dbnary:Gloss;
        #   dbnary:senseNumber "2" .
        #
        # Translation verweist anschließend auf diesen Gloss.

        if "dbnary:Gloss" in text:

            sense_number_match = re.search(
                r'dbnary:senseNumber\s+"([^"]+)"',
                text
            )

            if sense_number_match:

                gloss_to_sense_number[
                    subject
                ] = sense_number_match.group(1)

            return

        # ====================================================
        # 4. TRANSLATION
        # ====================================================

        if "dbnary:Translation" not in text:
            return

        # Welches deutsche LexicalEntry
        # wird übersetzt?

        source_match = re.search(
            r'dbnary:isTranslationOf\s+([^\s;]+)',
            text
        )

        if not source_match:
            return

        source_resource = source_match.group(1)

        source_entry = lexical_entries.get(
            source_resource
        )

        if not source_entry:
            return

        # Zielsprache

        language_match = re.search(
            r'dbnary:targetLanguage\s+'
            r'lexvo:([a-z]{3})',
            text
        )

        if not language_match:
            return

        target_iso3 = language_match.group(1)

        target_code = LANGUAGE_MAP.get(
            target_iso3
        )

        if not target_code:

            skipped_languages += 1
            return

        target_language_id = get_language_id(
            cursor,
            target_code
        )

        if target_language_id is None:

            skipped_languages += 1
            return

        # Zielwort

        written_match = re.search(
            r'dbnary:writtenForm\s+'
            r'"((?:[^"\\]|\\.)*)"@'
            r'([^\s.;]+)',
            text
        )

        if not written_match:
            return

        target_word = clean_turtle_string(
            written_match.group(1)
        )

        if not target_word:
            return

        target_word_id = get_or_create_word(
            cursor,
            target_language_id,
            target_word
        )

        source_word_id = source_entry[
            "word_id"
        ]

        # ====================================================
        # Alte Übersetzung weiterhin pflegen
        # ====================================================

        created = create_translation(
            cursor,
            source_word_id,
            target_word_id
        )

        if created:

            created_legacy_translations += 1

        # Rückrichtung weiterhin erzeugen.

        create_translation(
            cursor,
            target_word_id,
            source_word_id
        )

        # ====================================================
        # Bedeutung herausfinden
        # ====================================================

        gloss_match = re.search(
            r'dbnary:gloss\s+([^\s;]+)',
            text
        )

        if not gloss_match:

            translations_without_meaning += 1
            return

        gloss_resource = gloss_match.group(1)

        sense_number = gloss_to_sense_number.get(
            gloss_resource
        )

        if not sense_number:

            translations_without_meaning += 1
            return

        meaning_id = entry_sense_to_meaning.get(
            (
                source_resource,
                sense_number
            )
        )

        if not meaning_id:

            translations_without_meaning += 1
            return

        created = create_meaning_translation(
            cursor,
            meaning_id,
            target_word_id
        )

        if created:

            created_meaning_translations += 1

    # ========================================================
    # DATEI STREAMING VERARBEITEN
    # ========================================================

    current_subject = None
    current_block = []

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            for line_number, line in enumerate(
                file,
                start=1
            ):

                stripped = line.strip()

                if not stripped:
                    continue

                # Prefixe brauchen wir nicht.

                if stripped.startswith("@prefix"):
                    continue

                # Eine nicht eingerückte Zeile beginnt
                # einen neuen Turtle-Block.

                if not line[0].isspace():

                    if current_subject:

                        process_block(
                            current_subject,
                            current_block
                        )

                        processed_blocks += 1

                    parts = stripped.split(
                        None,
                        1
                    )

                    current_subject = parts[0]

                    current_block = []

                    if len(parts) > 1:

                        current_block.append(
                            parts[1]
                        )

                else:

                    current_block.append(
                        stripped
                    )

                # Regelmäßig committen.

                if (
                    processed_blocks > 0
                    and processed_blocks % 10000 == 0
                ):

                    connection.commit()

                    print(
                        "\r"
                        f"Blöcke: "
                        f"{processed_blocks:,} | "
                        f"Bedeutungen: "
                        f"{created_meanings:,} | "
                        f"Bedeutungsübersetzungen: "
                        f"{created_meaning_translations:,}",
                        end="",
                        flush=True
                    )

            # Letzten Block verarbeiten.

            if current_subject:

                process_block(
                    current_subject,
                    current_block
                )

        connection.commit()

    except KeyboardInterrupt:

        print()
        print()
        print("Import wurde abgebrochen.")

        connection.commit()

    except Exception as error:

        connection.rollback()

        print()
        print("Fehler beim Import:")
        print(error)

        raise

    finally:

        connection.close()

    # ========================================================
    # ERGEBNIS
    # ========================================================

    print()
    print()
    print("=" * 65)
    print("DBnary Import abgeschlossen")
    print()

    print(
        f"Blöcke verarbeitet:             "
        f"{processed_blocks:,}"
    )

    print(
        f"Bedeutungen verarbeitet:        "
        f"{created_meanings:,}"
    )

    print(
        f"Bedeutungsübersetzungen erstellt:"
        f" {created_meaning_translations:,}"
    )

    print(
        f"Neue alte Übersetzungen:         "
        f"{created_legacy_translations:,}"
    )

    print(
        f"Übersetzungen ohne Sense:        "
        f"{translations_without_meaning:,}"
    )

    print(
        f"Nicht unterstützte Sprachen:     "
        f"{skipped_languages:,}"
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    if len(sys.argv) < 2:

        print()
        print("Verwendung:")
        print(
            "python -m scripts.import_dbnary "
            "data/de_dbnary_ontolex.ttl"
        )

        sys.exit(1)

    import_dbnary(
        sys.argv[1]
    )