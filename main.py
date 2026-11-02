import tkinter as tk
from tkinter import ttk


def main():
    root = tk.Tk()

    root.title("Lernstick Übersetzung")
    root.geometry("800x550")
    root.minsize(700, 450)

    title = ttk.Label(
        root,
        text="Lernstick Übersetzung",
        font=("Arial", 22, "bold")
    )
    title.pack(pady=30)

    info = ttk.Label(
        root,
        text="Offline-Wörterbuch",
        font=("Arial", 12)
    )
    info.pack()

    root.mainloop()


if __name__ == "__main__":
    main()