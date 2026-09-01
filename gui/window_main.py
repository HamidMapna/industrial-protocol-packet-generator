import tkinter as tk
from tkinter import ttk


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Industrial Protocol Packet Generator")
        self.root.geometry("900x600")
        self.root.configure(bg="#f4f6f8")

        self.configure_styles()
        self.create_widgets()

    def configure_styles(self):
        style = ttk.Style()

        # Application title
        style.configure(
            "Title.TLabel",
            background="#1f4e78",
            foreground="white",
            font=("Segoe UI", 18, "bold"),
            padding=12
        )

        # Protocol section
        style.configure(
            "Protocol.TLabelframe",
            background="#F4B183",
            foreground="#7F3F00",
            font=("Segoe UI", 10, "bold")
        )

        style.configure(
            "Protocol.TLabelframe.Label",
            background="#F4B183",
            foreground="#7F3F00",
            font=("Segoe UI", 10, "bold")
        )

        style.configure(
            "Protocol.TLabel",
            background="#F4B183",
            foreground="#333333",
            font=("Segoe UI", 10)
        )

        style.configure(
            "Protocol.TCombobox",
            font=("Segoe UI", 10)
        )

    def create_widgets(self):
        title_label = ttk.Label(
            self.root,
            text="Industrial Protocol Packet Generator",
            style="Title.TLabel"
        )
        title_label.pack(
            fill="x",
            padx=10,
            pady=(10, 0)
        )

        protocol_frame = ttk.LabelFrame(
            self.root,
            text="Protocol",
            style="Protocol.TLabelframe"
        )
        protocol_frame.pack(
            fill="x",
            padx=10,
            pady=15
        )

        ttk.Label(
            protocol_frame,
            text="Protocol:",
            style="Protocol.TLabel"
        ).pack(
            side="left",
            padx=(10, 5),
            pady=12
        )

        self.protocol_var = tk.StringVar(
            value="IEC 60870-5-104"
        )

        self.protocol_combo = ttk.Combobox(
            protocol_frame,
            textvariable=self.protocol_var,
            state="readonly",
            values=[
                "IEC 60870-5-104",
                "Modbus TCP",
                "OPC UA",
            ],
            width=25,
            style="Protocol.TCombobox"
        )
        self.protocol_combo.pack(
            side="left",
            padx=5,
            pady=12
        )

        self.protocol_combo.bind(
            "<<ComboboxSelected>>",
            self.on_protocol_selected
        )

    def on_protocol_selected(self, event):
        protocol = self.protocol_var.get()
        print(f"Selected protocol: {protocol}")

    def run(self):
        self.root.mainloop()