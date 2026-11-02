import tkinter as tk
from tkinter import ttk

from database.database import get_languages
from services.translation_service import translate_word


class MainWindow:

    def __init__(self, root):
        self.root = root

        self.root.title("Lernstick Übersetzung")
        self.root.geometry("800x550")
        self.root.minsize(700, 450)

        # Sprachen aus der Datenbank laden
        self.languages = get_languages()

        # Beispiel:
        # Deutsch -> de
        # Koreanisch -> ko
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

        # Titel
        title = ttk.Label(
            self.root,
            text="Lernstick Übersetzung",
            font=("Arial", 22, "bold")
        )

        title.pack(
            pady=(30, 5)
        )

        subtitle = ttk.Label(
            self.root,
            text="Offline-Wörterbuch",
            font=("Arial", 11)
        )

        subtitle.pack(
            pady=(0, 25)
        )

        # Sprachbereich
        language_frame = ttk.Frame(
            self.root
        )

        language_frame.pack(
            pady=10
        )

        # Ausgangssprache
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

        # Sprachen tauschen
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

        # Zielsprache
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

        # Standardsprachen setzen
        if "Deutsch" in self.language_names:
            self.source_language.set(
                "Deutsch"
            )

        if "Englisch" in self.language_names:
            self.target_language.set(
                "Englisch"
            )

        # Eingabebereich
        input_label = ttk.Label(
            self.root,
            text="Wort eingeben:"
        )

        input_label.pack(
            pady=(35, 5)
        )

        self.input_entry = ttk.Entry(
            self.root,
            width=50,
            font=("Arial", 14)
        )

        self.input_entry.pack(
            pady=5
        )

        # Übersetzen
        translate_button = ttk.Button(
            self.root,
            text="Übersetzen",
            command=self.translate
        )

        translate_button.pack(
            pady=20
        )

        # Ergebnis
        result_title = ttk.Label(
            self.root,
            text="Übersetzung:",
            font=("Arial", 11, "bold")
        )

        result_title.pack()

        self.result_label = ttk.Label(
            self.root,
            text="",
            font=("Arial", 20),
            wraplength=650,
            justify="left"
        )

        self.result_label.pack(
            pady=15
        )

        # Enter-Taste = Übersetzen
        self.input_entry.bind(
            "<Return>",
            lambda event: self.translate()
        )

        # Cursor direkt ins Eingabefeld
        self.input_entry.focus()

    def swap_languages(self):

        source = self.source_language.get()
        target = self.target_language.get()

        self.source_language.set(target)
        self.target_language.set(source)

    def translate(self):

        word = self.input_entry.get().strip()

        if not word:
            self.result_label.config(
                text="Bitte ein Wort eingeben."
            )
            return

        source_name = self.source_language.get()
        target_name = self.target_language.get()

        if not source_name or not target_name:
            self.result_label.config(
                text="Bitte beide Sprachen auswählen."
            )
            return

        # Gleiche Ausgangs- und Zielsprache
        if source_name == target_name:
            self.result_label.config(
                text=word
            )
            return

        source_code = self.language_codes[
            source_name
        ]

        target_code = self.language_codes[
            target_name
        ]

        translations = translate_word(
            word,
            source_code,
            target_code
        )

        if translations:

            if len(translations) == 1:

                result_text = translations[0]

            else:

                result_text = "\n".join(
                    f"• {translation}"
                    for translation in translations
                )

            self.result_label.config(
                text=result_text
            )

        else:

            self.result_label.config(
                text="Keine Übersetzung gefunden."
            )