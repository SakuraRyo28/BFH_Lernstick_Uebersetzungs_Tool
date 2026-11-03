import tkinter as tk
from tkinter import ttk

from database.database import get_languages
from services.translation_service import translate


class MainWindow:

    def __init__(self, root):

        self.root = root

        self.root.title("Lernstick Übersetzung")
        self.root.geometry("900x650")
        self.root.minsize(750, 550)

        # Sprachen aus SQLite laden
        self.languages = get_languages()

        self.language_codes = {
            name: code
            for code, name in self.languages
        }

        self.language_names = [
            name
            for code, name in self.languages
        ]

        self.create_widgets()

    def create_widgets(self):

        # =====================================================
        # TITEL
        # =====================================================

        title = ttk.Label(
            self.root,
            text="Lernstick Übersetzung",
            font=("Arial", 22, "bold")
        )

        title.pack(
            pady=(25, 5)
        )

        subtitle = ttk.Label(
            self.root,
            text="Offline-Wörterbuch",
            font=("Arial", 11)
        )

        subtitle.pack(
            pady=(0, 20)
        )

        # =====================================================
        # SPRACHAUSWAHL
        # =====================================================

        language_frame = ttk.Frame(
            self.root
        )

        language_frame.pack(
            pady=10
        )

        source_label = ttk.Label(
            language_frame,
            text="Ausgangssprache"
        )

        source_label.grid(
            row=0,
            column=0,
            padx=10,
            pady=5
        )

        self.source_language = ttk.Combobox(
            language_frame,
            values=self.language_names,
            state="readonly",
            width=28
        )

        self.source_language.grid(
            row=1,
            column=0,
            padx=10
        )

        swap_button = ttk.Button(
            language_frame,
            text="⇄",
            command=self.swap_languages
        )

        swap_button.grid(
            row=1,
            column=1,
            padx=10
        )

        target_label = ttk.Label(
            language_frame,
            text="Zielsprache"
        )

        target_label.grid(
            row=0,
            column=2,
            padx=10,
            pady=5
        )

        self.target_language = ttk.Combobox(
            language_frame,
            values=self.language_names,
            state="readonly",
            width=28
        )

        self.target_language.grid(
            row=1,
            column=2,
            padx=10
        )

        # Standardsprachen

        if "Deutsch" in self.language_names:

            self.source_language.set(
                "Deutsch"
            )

        if "Englisch" in self.language_names:

            self.target_language.set(
                "Englisch"
            )

        # =====================================================
        # WORTEINGABE
        # =====================================================

        input_label = ttk.Label(
            self.root,
            text="Wort eingeben:"
        )

        input_label.pack(
            pady=(25, 5)
        )

        self.input_entry = ttk.Entry(
            self.root,
            width=45,
            font=("Arial", 15)
        )

        self.input_entry.pack(
            pady=5
        )

        self.input_entry.bind(
            "<Return>",
            lambda event: self.translate_word()
        )

        # =====================================================
        # ÜBERSETZEN
        # =====================================================

        translate_button = ttk.Button(
            self.root,
            text="Übersetzen",
            command=self.translate_word
        )

        translate_button.pack(
            pady=15
        )

        # =====================================================
        # ERGEBNISBEREICH
        # =====================================================

        result_title = ttk.Label(
            self.root,
            text="Übersetzung",
            font=("Arial", 12, "bold")
        )

        result_title.pack(
            pady=(5, 5)
        )

        result_frame = ttk.Frame(
            self.root
        )

        result_frame.pack(
            fill="both",
            expand=True,
            padx=40,
            pady=(0, 30)
        )

        # Scrollbar

        scrollbar = ttk.Scrollbar(
            result_frame,
            orient="vertical"
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        # Textfeld

        self.result_text = tk.Text(
            result_frame,
            wrap="word",
            font=("Arial", 12),
            padx=15,
            pady=15,
            yscrollcommand=scrollbar.set
        )

        self.result_text.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.config(
            command=self.result_text.yview
        )

        # Benutzer soll Ergebnis nicht bearbeiten

        self.result_text.config(
            state="disabled"
        )

        # Formatierung

        self.result_text.tag_configure(
            "word",
            font=("Arial", 18, "bold"),
            spacing3=10
        )

        self.result_text.tag_configure(
            "word_type",
            font=("Arial", 12, "italic"),
            foreground="#555555",
            spacing3=8
        )

        self.result_text.tag_configure(
            "sense",
            font=("Arial", 12, "bold"),
            spacing1=8,
            spacing3=3
        )

        self.result_text.tag_configure(
            "definition",
            font=("Arial", 12),
            spacing3=6
        )

        self.result_text.tag_configure(
            "translation",
            font=("Arial", 14),
            spacing3=3
        )

        self.result_text.tag_configure(
            "info",
            font=("Arial", 11, "italic"),
            foreground="#666666"
        )

        self.input_entry.focus()

    # =========================================================
    # SPRACHEN TAUSCHEN
    # =========================================================

    def swap_languages(self):

        source = self.source_language.get()
        target = self.target_language.get()

        self.source_language.set(
            target
        )

        self.target_language.set(
            source
        )

    # =========================================================
    # RESULTATFELD LEEREN
    # =========================================================

    def clear_result(self):

        self.result_text.config(
            state="normal"
        )

        self.result_text.delete(
            "1.0",
            tk.END
        )

    # =========================================================
    # RESULTATFELD SPERREN
    # =========================================================

    def lock_result(self):

        self.result_text.config(
            state="disabled"
        )

    # =========================================================
    # ÜBERSETZEN
    # =========================================================

    def translate_word(self):

        word = self.input_entry.get().strip()

        self.clear_result()

        if not word:

            self.result_text.insert(
                tk.END,
                "Bitte ein Wort eingeben.",
                "info"
            )

            self.lock_result()

            return

        source_name = self.source_language.get()
        target_name = self.target_language.get()

        if not source_name or not target_name:

            self.result_text.insert(
                tk.END,
                "Bitte beide Sprachen auswählen.",
                "info"
            )

            self.lock_result()

            return

        if source_name == target_name:

            self.result_text.insert(
                tk.END,
                word,
                "word"
            )

            self.lock_result()

            return

        source_code = self.language_codes[
            source_name
        ]

        target_code = self.language_codes[
            target_name
        ]

        # =====================================================
        # SERVICE AUFRUFEN
        # =====================================================

        result = translate(
            word,
            source_code,
            target_code
        )

        # Suchwort anzeigen

        self.result_text.insert(
            tk.END,
            f"{word}\n",
            "word"
        )

        # =====================================================
        # BEDEUTUNGSBASIERTE ERGEBNISSE
        # =====================================================

        if result["type"] == "meanings":

            meanings = result["results"]

            current_word_type = None

            for meaning in meanings:

                word_type = meaning.get(
                    "part_of_speech"
                )

                sense_number = meaning.get(
                    "sense_number"
                )

                definition = meaning.get(
                    "definition"
                )

                translations = meaning.get(
                    "translations",
                    []
                )

                # Wortart nur anzeigen,
                # wenn sie vorhanden ist.

                if (
                    word_type
                    and word_type != current_word_type
                ):

                    self.result_text.insert(
                        tk.END,
                        f"{word_type}\n\n",
                        "word_type"
                    )

                    current_word_type = word_type

                # Bedeutung

                if sense_number:

                    self.result_text.insert(
                        tk.END,
                        f"Bedeutung {sense_number}\n",
                        "sense"
                    )

                else:

                    self.result_text.insert(
                        tk.END,
                        "Bedeutung\n",
                        "sense"
                    )

                # Definition

                if definition:

                    self.result_text.insert(
                        tk.END,
                        f"{definition}\n",
                        "definition"
                    )

                # Zielsprache

                self.result_text.insert(
                    tk.END,
                    f"\n{target_name}:\n",
                    "sense"
                )

                # Übersetzungen

                for translation_word in translations:

                    self.result_text.insert(
                        tk.END,
                        f"• {translation_word}\n",
                        "translation"
                    )

                self.result_text.insert(
                    tk.END,
                    "\n"
                )

        # =====================================================
        # FALLBACK OHNE BEDEUTUNG
        # =====================================================

        else:

            translations = result["results"]

            if translations:

                self.result_text.insert(
                    tk.END,
                    f"{target_name}:\n\n",
                    "sense"
                )

                for translation_word in translations:

                    self.result_text.insert(
                        tk.END,
                        f"• {translation_word}\n",
                        "translation"
                    )

                self.result_text.insert(
                    tk.END,
                    "\n"
                )

                self.result_text.insert(
                    tk.END,
                    "Für dieses Wort sind noch keine "
                    "Bedeutungsinformationen verfügbar.",
                    "info"
                )

            else:

                self.result_text.insert(
                    tk.END,
                    "\nKeine Übersetzung gefunden.",
                    "info"
                )

        self.lock_result()