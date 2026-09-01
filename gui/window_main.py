import tkinter as tk


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Industrial Protocol Packet Generator")
        self.root.geometry("900x600")

        self.create_widgets()

    def create_widgets(self):
        pass

    def run(self):
        self.root.mainloop()