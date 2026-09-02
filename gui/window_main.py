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
        "Connection.TLabelframe",
        background="#D9EAF7",
        foreground="#1F4E78",
        font=("Segoe UI", 10, "bold")
        )

        style.configure(
            "Connection.TLabelframe.Label",
            background="#D9EAF7",
            foreground="#1F4E78",
            font=("Segoe UI", 10, "bold")
        )

        style.configure(
            "Connection.TLabel",
            background="#D9EAF7",
            foreground="#333333",
            font=("Segoe UI", 10)
        )

        style.configure(
            "Connection.TEntry",
            font=("Segoe UI", 10)
        )

        style.configure(
            "Connection.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(10, 5)
        )

        style.configure(
            "Protocol.TCombobox",
            font=("Segoe UI", 10)
        )
        
        style.configure(
        "Packet.TLabelframe",
        background="#E2F0D9",
        foreground="#548235",
        font=("Segoe UI", 10, "bold")
    )

    style.configure(
        "Packet.TLabelframe.Label",
        background="#E2F0D9",
        foreground="#548235",
        font=("Segoe UI", 10, "bold")
    )

    style.configure(
        "Packet.TLabel",
        background="#E2F0D9",
        foreground="#333333",
        font=("Segoe UI", 10)
    )

    style.configure(
        "Packet.TCombobox",
        font=("Segoe UI", 10)
    )

    style.configure(
        "Packet.TEntry",
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
        
        connection_frame = ttk.LabelFrame(
            self.root,
            text="Connection",
            style="Connection.TLabelframe"
        )
        connection_frame.pack(
            fill="x",
            padx=10,
            pady=(0, 15)
        )

        ttk.Label(
            connection_frame,
            text="Server IP:",
            style="Connection.TLabel"
        ).grid(
            row=0,
            column=0,
            padx=(10, 5),
            pady=10,
            sticky="w"
        )

        self.server_ip_var = tk.StringVar(
            value="192.168.42.185"
        )

        self.server_ip_entry = ttk.Entry(
            connection_frame,
            textvariable=self.server_ip_var,
            width=20,
            style="Connection.TEntry"
        )
        self.server_ip_entry.grid(
            row=0,
            column=1,
            padx=5,
            pady=10
        )

        ttk.Label(
            connection_frame,
            text="Server Port:",
            style="Connection.TLabel"
        ).grid(
            row=0,
            column=2,
            padx=(20, 5),
            pady=10,
            sticky="w"
        )

        self.server_port_var = tk.StringVar(
            value="2404"
        )

        self.server_port_entry = ttk.Entry(
            connection_frame,
            textvariable=self.server_port_var,
            width=8,
            style="Connection.TEntry"
        )
        self.server_port_entry.grid(
            row=0,
            column=3,
            padx=5,
            pady=10
        )

        self.connect_button = ttk.Button(
            connection_frame,
            text="Connect",
            style="Connection.TButton",
            command=self.on_connect
        )
        self.connect_button.grid(
            row=0,
            column=4,
            padx=(20, 5),
            pady=10
        )

        self.disconnect_button = ttk.Button(
            connection_frame,
            text="Disconnect",
            style="Connection.TButton",
            command=self.on_disconnect,
            state="disabled"
        )
        self.disconnect_button.grid(
            row=0,
            column=5,
            padx=5,
            pady=10
        )

        self.connection_status_var = tk.StringVar(
            value="Disconnected"
        )

        ttk.Label(
            connection_frame,
            textvariable=self.connection_status_var,
            style="Connection.TLabel"
        ).grid(
            row=0,
            column=6,
            padx=(20, 10),
            pady=10
        )
        
        packet_frame = ttk.LabelFrame(
        self.root,
        text="Packet Specification",
        style="Packet.TLabelframe"
        )
        packet_frame.pack(
            fill="x",
            padx=10,
            pady=(0, 15)
        )
        
        ttk.Label(
            packet_frame,
            text="Frame Type:",
            style="Packet.TLabel"
        ).grid(
            row=0,
            column=0,
            padx=(10, 5),
            pady=10,
            sticky="w"
        )

        self.frame_type_var = tk.StringVar(
            value="I-format"
        )

        self.frame_type_combo = ttk.Combobox(
            packet_frame,
            textvariable=self.frame_type_var,
            state="readonly",
            values=[
                "I-format",
                "S-format",
                "U-format"
            ],
            width=15,
            style="Packet.TCombobox"
        )

        self.frame_type_combo.grid(
            row=0,
            column=1,
            padx=5,
            pady=10
        )

        self.frame_type_combo.bind(
            "<<ComboboxSelected>>",
            self.on_frame_type_selected
        )
        
        ttk.Label(
            packet_frame,
            text="Type ID:",
            style="Packet.TLabel"
        ).grid(
            row=0,
            column=2,
            padx=(20, 5),
            pady=10,
            sticky="w"
        )

        self.type_id_var = tk.StringVar(
            value="45"
        )

        self.type_id_combo = ttk.Combobox(
            packet_frame,
            textvariable=self.type_id_var,
            state="readonly",
            values=[
                "45 - M_SP_NA_1",
                "46 - M_DP_NA_1",
                "47 - M_ST_NA_1",
                "48 - M_BO_NA_1",
                "49 - M_ME_NA_1",
                "50 - M_ME_NB_1",
            ],
            width=22,
            style="Packet.TCombobox"
        )

        self.type_id_combo.grid(
            row=0,
            column=3,
            padx=5,
            pady=10
        )
        
        ttk.Label(
            packet_frame,
            text="VSQ:",
            style="Packet.TLabel"
        ).grid(
            row=0,
            column=4,
            padx=(20, 5),
            pady=10,
            sticky="w"
        )

        self.vsq_var = tk.StringVar(
            value="1"
        )

        self.vsq_entry = ttk.Entry(
            packet_frame,
            textvariable=self.vsq_var,
            width=8,
            style="Packet.TEntry"
        )

        self.vsq_entry.grid(
            row=0,
            column=5,
            padx=5,
            pady=10
        )

    def on_protocol_selected(self, event):
        protocol = self.protocol_var.get()
        print(f"Selected protocol: {protocol}")
        
    def on_connect(self):
        server_ip = self.server_ip_var.get()
        server_port = self.server_port_var.get()

        print(f"Connect to {server_ip}:{server_port}")

        self.connection_status_var.set("Connected")
        self.connect_button.config(state="disabled")
        self.disconnect_button.config(state="normal")


    def on_disconnect(self):
        print("Disconnect")

        self.connection_status_var.set("Disconnected")
        self.connect_button.config(state="normal")
        self.disconnect_button.config(state="disabled")    

    def run(self):
        self.root.mainloop()