import tkinter as tk

from database.database import create_database, insert_languages
from gui.main_window import MainWindow


def main():

    # Datenbank initialisieren
    create_database()

    # Sprachen einfügen
    insert_languages()

    # GUI starten
    root = tk.Tk()

    MainWindow(root)

    root.mainloop()


if __name__ == "__main__":
    main()