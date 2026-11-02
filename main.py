import tkinter as tk

from database.database import create_database, insert_languages
from gui.main_window import MainWindow


def main():
    # Datenbank und Tabellen erstellen,
    # falls sie noch nicht vorhanden sind
    create_database()

    # Unterstützte Sprachen eintragen
    insert_languages()

    # GUI starten
    root = tk.Tk()

    MainWindow(root)

    root.mainloop()


if __name__ == "__main__":
    main()