import socket
import argparse


# ============================================================
# Configuration
# ============================================================

DEST_IP = "192.168.42.185"
DEST_PORT = 2404

SOCKET_TIMEOUT = 5

COMMON_ADDRESS = 3
IOA = 2

# ============================================================
# IEC-104 Type IDs
# ============================================================

TYPE_SINGLE_COMMAND = 46       # C_SC_NA_1
TYPE_CLOCK_SYNC = 103           # C_CS_NA_1
TYPE_GENERAL_INTERROGATION = 100  # C_IC_NA_1
TYPE_COUNTER_INTERROGATION = 101  # C_CI_NA_1

# ============================================================
# IEC-104 parameters
# ============================================================

VSQ = 0x01

COT_ACTIVATION = 6
ORIGINATOR_ADDRESS = 4

# Single command
SCO = 0x00


# ============================================================
# Basic helpers
# ============================================================

def le16(value):
    """Encode an unsigned 16-bit value as little-endian."""
    return bytes([
        value & 0xFF,
        (value >> 8) & 0xFF
    ])


def iec104_sequence(value):
    """
    IEC-104 encodes N(S)/N(R) as value << 1.
    """
    return le16(value << 1)


# ============================================================
# IEC-104 U-format
# ============================================================

def build_startdt_act():
    return bytes([
        0x68,
        0x04,
        0x07,
        0x00,
        0x00,
        0x00
    ])


def is_startdt_con(packet):
    return packet == bytes([
        0x68,
        0x04,
        0x0B,
        0x00,
        0x00,
        0x00
    ])


# ============================================================
# IEC-104 S-format
# ============================================================

def build_s_frame(recv_seq):
    """
    Build S-format acknowledgement.

        68 04
        01 00
        N(R) << 1

    Example:
        N(R)=9 -> 12 00
    """

    nr = iec104_sequence(recv_seq)

    return bytes([
        0x68,
        0x04,
        0x01,
        0x00,
        nr[0],
        nr[1]
    ])


# ============================================================
# ASDU builders
# ============================================================

def build_single_command_asdu():
    """
    C_SC_NA_1

    2d 01 06 04 03 00 01 00 00 01
    """

    asdu = bytearray()

    asdu.append(TYPE_SINGLE_COMMAND)
    asdu.append(VSQ)

    # COT = 6
    asdu.append(COT_ACTIVATION)

    # OA = 4
    asdu.append(ORIGINATOR_ADDRESS)

    # Common Address = 3
    asdu.extend(le16(COMMON_ADDRESS))

    # IOA = 1, three bytes
    asdu.append(IOA & 0xFF)
    asdu.append((IOA >> 8) & 0xFF)
    asdu.append((IOA >> 16) & 0xFF)

    # SCO
    asdu.append(SCO)

    return bytes(asdu)


def build_clock_sync_asdu():
    """
    C_CS_NA_1.

    The harness sends:

        67 01 06 04 03 00
        00 00 00
        <CP56Time2a>

    We reproduce the structure seen in the trace.

    The time value can be replaced later with a dynamically
    generated CP56Time2a value if required.
    """

    asdu = bytearray()

    asdu.append(TYPE_CLOCK_SYNC)
    asdu.append(VSQ)

    asdu.append(COT_ACTIVATION)
    asdu.append(ORIGINATOR_ADDRESS)

    asdu.extend(le16(COMMON_ADDRESS))

    # IOA = 0
    asdu.extend(b"\x00\x00\x00")

    # CP56Time2a from the harness example
    asdu.extend(bytes([
        0x2F,
        0xBC,
        0x0F,
        0x17,
        0xDD,
        0x08
    ]))

    return bytes(asdu)


def build_general_interrogation_asdu():
    """
    C_IC_NA_1

    Harness:

        64 01 06 04 03 00 00 00 00 14
    """

    asdu = bytearray()

    asdu.append(TYPE_GENERAL_INTERROGATION)
    asdu.append(VSQ)

    asdu.append(COT_ACTIVATION)
    asdu.append(ORIGINATOR_ADDRESS)

    asdu.extend(le16(COMMON_ADDRESS))

    # IOA = 0
    asdu.extend(b"\x00\x00\x00")

    # QOI = 20
    asdu.append(0x14)

    return bytes(asdu)


def build_counter_interrogation_asdu():
    """
    C_CI_NA_1

    Harness:

        65 01 06 04 03 00 00 00 00 05
    """

    asdu = bytearray()

    asdu.append(TYPE_COUNTER_INTERROGATION)
    asdu.append(VSQ)

    asdu.append(COT_ACTIVATION)
    asdu.append(ORIGINATOR_ADDRESS)

    asdu.extend(le16(COMMON_ADDRESS))

    # IOA = 0
    asdu.extend(b"\x00\x00\x00")

    # QCC = 5
    asdu.append(0x05)

    return bytes(asdu)


# ============================================================
# I-format
# ============================================================

def build_i_frame(asdu, send_seq, recv_seq, abnormal=False):
    """
    Build an IEC-104 I-format APDU.

    Normal:

        C1/C2 = N(S) << 1
        C3/C4 = N(R) << 1

    Abnormal:

        Set only bit 0 of C1 after constructing the legitimate
        sequence number.
    """

    ns = bytearray(iec104_sequence(send_seq))
    nr = iec104_sequence(recv_seq)

    # --------------------------------------------------------
    # The legitimate N(S) is already encoded in ns[0]/ns[1].
    #
    # For the abnormal test, change ONLY C1 bit 0.
    # --------------------------------------------------------

    if abnormal:
        ns[0] |= 0x01

    control = bytes(ns) + nr

    information_field = control + asdu

    return bytes([
        0x68,
        len(information_field)
    ]) + information_field


# ============================================================
# APDU reception
# ============================================================

def recv_exact(sock, count):
    data = bytearray()

    while len(data) < count:

        chunk = sock.recv(count - len(data))

        if not chunk:
            return None

        data.extend(chunk)

    return bytes(data)


def recv_apdu(sock):

    header = recv_exact(sock, 2)

    if header is None:
        return None

    if header[0] != 0x68:
        raise ValueError(
            "Invalid IEC-104 start byte: "
            "0x{:02X}".format(header[0])
        )

    length = header[1]

    body = recv_exact(sock, length)

    if body is None:
        return None

    return header + body


# ============================================================
# Sequence decoding
# ============================================================

def get_ns(packet):
    """
    Get N(S) from an I-format packet.
    """

    if len(packet) < 6:
        return None

    value = packet[2] | (packet[3] << 8)

    if value & 0x01:
        return None

    return value >> 1


def get_nr(packet):
    """
    Get N(R) from C3/C4.
    """

    if len(packet) < 6:
        return None

    value = packet[4] | (packet[5] << 8)

    return value >> 1


def is_i_format(packet):
    return (
        len(packet) >= 6 and
        (packet[2] & 0x01) == 0
    )


def is_s_format(packet):
    return (
        len(packet) >= 6 and
        (packet[2] & 0x03) == 0x01
    )


def is_u_format(packet):
    return (
        len(packet) >= 6 and
        (packet[2] & 0x03) == 0x03
    )


# ============================================================
# Session
# ============================================================

class IEC104Session:

    def __init__(self, sock):

        self.sock = sock

        # Client transmit sequence
        self.send_seq = 0

        # Next server sequence number expected/acknowledged
        self.recv_seq = 0

    # --------------------------------------------------------
    # Send
    # --------------------------------------------------------

    def send_i(self, asdu, abnormal=False):

        packet = build_i_frame(
            asdu,
            self.send_seq,
            self.recv_seq,
            abnormal
        )

        print()
        print("CLIENT I-FRAME")
        print("  N(S) =", self.send_seq)
        print("  N(R) =", self.recv_seq)
        print("  HEX  =", packet.hex(" "))

        self.sock.sendall(packet)

        # Advance client's N(S) after transmission.
        self.send_seq += 1

        return packet

    # --------------------------------------------------------
    # Receive
    # --------------------------------------------------------

    def receive(self):

        packet = recv_apdu(self.sock)

        if packet is None:
            return None

        print()
        print("SERVER FRAME")
        print("  HEX =", packet.hex(" "))

        # ----------------------------------------------------
        # I-format
        # ----------------------------------------------------

        if is_i_format(packet):

            server_ns = get_ns(packet)
            server_nr = get_nr(packet)

            print("  Format = I")
            print("  Server N(S) =", server_ns)
            print("  Server N(R) =", server_nr)

            # The server has delivered an I-frame with N(S).
            #
            # We have received that frame, therefore the next
            # server sequence number we acknowledge is NS + 1.
            if server_ns is not None:

                self.recv_seq = server_ns + 1

                print(
                    "  Client N(R) updated to",
                    self.recv_seq
                )

            return packet

        # ----------------------------------------------------
        # S-format
        # ----------------------------------------------------

        if is_s_format(packet):

            print("  Format = S")
            print("  Server N(R) =", get_nr(packet))

            return packet

        # ----------------------------------------------------
        # U-format
        # ----------------------------------------------------

        if is_u_format(packet):

            print("  Format = U")

            return packet

        print("  Unknown format")

        return packet

    # --------------------------------------------------------
    # Wait for STARTDT_CON
    # --------------------------------------------------------
    def start_data_transfer(self):
        packet = build_startdt_act()

        print()
        print("CLIENT:")
        print("  STARTDT_ACT")
        print(" ", packet.hex(" "))

        self.sock.sendall(packet)

        print()
        print("Waiting for STARTDT_CON ...")

        response = self.receive()

        if response is None:
            raise RuntimeError(
                "Connection closed while waiting for STARTDT_CON"
            )

        if is_startdt_con(response):
            print()
            print("STARTDT_CON received.")
            print("IEC-104 session is ONLINE.")
            return None

        if is_i_format(response):
            print()
            print("No STARTDT_CON received.")
            print("Initial server I-frame received.")
            print("IEC-104 session is ONLINE.")
            return response

        raise RuntimeError(
            "Expected STARTDT_CON or initial I-frame, received: {}".format(
                response.hex(" ")
            )
        )
        # --------------------------------------------------------
        # Receive initial server frame
        # --------------------------------------------------------

    def synchronize_initial_state(self):

        print()
        print("Waiting for server initialization frame...")

        packet = self.receive()

        if packet is None:
            raise RuntimeError(
                "Server closed connection."
            )

        if not is_i_format(packet):

            raise RuntimeError(
                "Expected initial I-frame, received: {}".format(
                    packet.hex(" ")
                )
            )

        print()
        print("Initial IEC-104 server state established.")
        print("Client N(S) =", self.send_seq)
        print("Client N(R) =", self.recv_seq)

        # --------------------------------------------------------
        # Initialization sequence
        # --------------------------------------------------------

    def perform_initialization(self):

        print()
        print("=" * 60)
        print("IEC-104 INITIALIZATION")
        print("=" * 60)

        # ----------------------------------------------------
        # 1. Clock synchronization
        # ----------------------------------------------------

        print()
        print("Sending Clock Synchronization request...")

        self.send_i(
            build_clock_sync_asdu()
        )

        response = self.receive()

        if response is not None:
            self.process_response(response)

        # ----------------------------------------------------
        # 2. General interrogation
        # ----------------------------------------------------

        print()
        print("Sending General Interrogation...")

        self.send_i(
            build_general_interrogation_asdu()
        )

        response = self.receive()

        if response is not None:
            self.process_response(response)

        # ----------------------------------------------------
        # 3. Counter interrogation
        # ----------------------------------------------------

        print()
        print("Sending Counter Interrogation...")

        self.send_i(
            build_counter_interrogation_asdu()
        )

        response = self.receive()

        if response is not None:
            self.process_response(response)

        # --------------------------------------------------------
        # Process server response
        # --------------------------------------------------------

    def process_response(self, packet):

        # ----------------------------------------------------
        # If I-frame, N(R) was already updated by receive().
        # ----------------------------------------------------

        if is_i_format(packet):

            print()
            print(
                "Updated session state:"
            )

            print(
                "  Client N(S) =",
                self.send_seq
            )

            print(
                "  Client N(R) =",
                self.recv_seq
            )

        # --------------------------------------------------------
        # Send acknowledgement
        # --------------------------------------------------------

    def send_s_ack(self):

        packet = build_s_frame(
            self.recv_seq
        )

        print()
        print("CLIENT S-FRAME")
        print("  N(R) =", self.recv_seq)
        print("  HEX  =", packet.hex(" "))

        self.sock.sendall(packet)


# ============================================================
# Main request
# ============================================================

def test_connection():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.settimeout(5)

        print(
            "Connecting to {}:{} ...".format(
                DEST_IP,
                DEST_PORT
            )
        )

        sock.connect((DEST_IP, DEST_PORT))

        print("TCP connection established.")

        start_act = bytes.fromhex(
            "68 04 07 00 00 00"
        )

        print()
        print("Sending STARTDT_ACT:")
        print(" ", start_act.hex(" "))

        sock.sendall(start_act)

        print()
        print("Waiting for ANY response...")

        try:
            data = sock.recv(4096)

            if data:
                print()
                print(
                    "Received {} bytes:".format(
                        len(data)
                    )
                )

                print(
                    data.hex(" ")
                )

            else:
                print(
                    "Server closed the connection."
                )

        except socket.timeout:
            print(
                "NO DATA RECEIVED within 5 seconds."
            )

    except Exception as e:
        print(
            "ERROR:",
            e
        )

    finally:
        sock.close()

        print(
            "Socket closed."
        )
        
def run_test(abnormal):

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    try:

        sock.settimeout(SOCKET_TIMEOUT)

        print()
        print(
            "Connecting to {}:{} ...".format(
                DEST_IP,
                DEST_PORT
            )
        )

        sock.connect(
            (DEST_IP, DEST_PORT)
        )

        print("TCP connection established.")

        # ----------------------------------------------------
        # Create IEC-104 session
        # ----------------------------------------------------

        session = IEC104Session(sock)

        initial_packet = session.start_data_transfer()

        if initial_packet is not None:
            # STARTDT_CON was not received because the initial I-frame
            # arrived first. It has already been processed by receive().
            print()
            print("Initial IEC-104 server state established.")
            print("Client N(S) =", session.send_seq)
            print("Client N(R) =", session.recv_seq)
        else:
            session.synchronize_initial_state()      

        # ----------------------------------------------------
        # Reproduce the initialization traffic seen in the
        # test harness.
        # ----------------------------------------------------

        session.perform_initialization()

        # ----------------------------------------------------
        # At this point the server may have sent several I
        # frames. We need to continue reading until the
        # initialization sequence has settled.
        #
        # For the trace supplied, the client eventually
        # acknowledges server frames with:
        #
        #     68 04 01 00 12 00
        #
        # which means N(R)=9.
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print("INITIALIZATION COMPLETE")
        print("=" * 60)

        print(
            "Current client N(S) =",
            session.send_seq
        )

        print(
            "Current client N(R) =",
            session.recv_seq
        )

        # ----------------------------------------------------
        # Send an S acknowledgement.
        #
        # This corresponds to the harness:
        #
        # 68 04 01 00 12 00
        #
        # when recv_seq == 9.
        # ----------------------------------------------------

        session.send_s_ack()

        # ----------------------------------------------------
        # Now send the actual C_SC_NA_1 command.
        # ----------------------------------------------------

        print()
        print("=" * 60)

        if abnormal:
            print("SENDING ABNORMAL C_SC_NA_1")
        else:
            print("SENDING NORMAL C_SC_NA_1")

        print("=" * 60)

        packet = session.send_i(
            build_single_command_asdu(),
            abnormal=abnormal
        )

        print()
        print("Command packet:")
        print(packet.hex(" "))

        # ----------------------------------------------------
        # Wait for server response.
        # ----------------------------------------------------

        print()
        print("Waiting for server response...")

        response = session.receive()

        if response is not None:

            print()
            print("Server response:")
            print(response.hex(" "))

            # ------------------------------------------------
            # If this is the positive activation confirmation:
            #
            # 2d 01 07 00 ...
            #
            # then the server accepted the command.
            # ------------------------------------------------

            if (
                len(response) >= 16 and
                response[6] == TYPE_SINGLE_COMMAND
            ):

                cot = response[8]

                print()
                print(
                    "Received C_SC_NA_1 response."
                )

                print(
                    "COT =",
                    cot
                )

                if cot == 7:
                    print(
                        "Positive activation confirmation."
                    )

                elif cot == 10:
                    print(
                        "Activation termination."
                    )

        print()
        print("Session test completed.")

    except socket.timeout:

        print()
        print(
            "ERROR: Socket timeout."
        )

    except ConnectionRefusedError:

        print()
        print(
            "ERROR: Connection refused."
        )

    except OSError as e:

        print()
        print(
            "ERROR:",
            e
        )

    finally:

        sock.close()

        print()
        print("TCP connection closed.")


# ============================================================
# Main
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description="IEC-104 session-based C_SC_NA_1 test"
    )

    parser.add_argument(
        "--normal",
        action="store_true",
        help="Send normal I-format C_SC_NA_1"
    )

    args = parser.parse_args()

    run_test(
        abnormal=not args.normal
    )


if __name__ == "__main__":
    #test_connection()
    main()