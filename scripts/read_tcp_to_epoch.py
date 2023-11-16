"""
Read data sent by Micromed through TCP.
In this case, we use a circular buffer of epoch_duration seconds with epoch_overlap seconds
overlap emulating a sliding window. Each time the buffer is filled in the next slided window,
update_epoch_buffer() returns True and one can access to the window.

HOW TO USE:
> python read_tcp_to_epoch.py --help
> python read_tcp_to_epoch.py
"""
import socket

import numpy as np

from micromed_io.buffer import MicromedBuffer
from micromed_io.tcp import decode_tcp_header_packet, MicromedPacketType
import logging
import argparse

if __name__ == "__main__":
    logging.basicConfig(level=0, format=("%(asctime)s\t\t%(levelname)s\t\t%(message)s"))
    parser = argparse.ArgumentParser(description="Read data from a Micromed TCP client")
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=5123,
        help="The TCP port number to connect to. The default is 5123.",
    )
    parser.add_argument(
        "-a",
        "--address",
        type=str,
        default="localhost",
        help="the TCP address to connect to. The default is localhost",
    )
    parser.add_argument(
        "-v",
        "--verbosity",
        type=int,
        choices=[0, 1, 2],
        default=1,
        help="Increase output verbosity. The default is 1.",
    )
    args = parser.parse_args()

    # convert to variable
    tcp_port = args.port
    tcp_address = args.address
    verbosity = args.verbosity

    # create micromed
    micromed_buffer = MicromedBuffer(epoch_duration=5, epoch_overlap=2.5)

    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the port
    server_address = (tcp_address, tcp_port)
    if verbosity >= 1:
        logging.info("starting up on %s port %s" % server_address)
    sock.bind(server_address)
    sock.listen(1)

    sock.settimeout(5)
    DONE = False
    connection = None

    if verbosity >= 1:
        logging.info("Waiting for a connection...")
    while connection is None:
        # Wait for a connection
        try:
            connection, client_address = sock.accept()
            if verbosity >= 1:
                logging.info("Connection from %s port %s" % server_address)
        except Exception as e:
            logging.warning(e)

    sock.settimeout(None)

    try:
        while True:
            header = connection.recv(2048)  # 10 is enoughbut more is fine too
            b_header = bytearray(header)
            packet_type, next_packet_size = decode_tcp_header_packet(b_header)

            if packet_type is not None:
                data = connection.recv(next_packet_size)
                b_data = bytearray(data)

                if packet_type == MicromedPacketType.HEADER:
                    micromed_buffer.decode_data_header_packet(b_data)
                    if verbosity >= 1:
                        logging.info("Micromed header")
                        print(micromed_buffer.micromed_header)

                elif packet_type == MicromedPacketType.EEG_DATA:
                    if not micromed_buffer.decode_data_eeg_packet(b_data):
                        logging.error("Error in EEG data packet")
                    if micromed_buffer.update_epoch_buffer():
                        logging.info("Buffer full:")
                        print(micromed_buffer.current_epoch.shape)
                        print(micromed_buffer.current_epoch)

                elif packet_type == MicromedPacketType.NOTE:
                    # TODO: check tcp note parsing
                    micromed_buffer.decode_operator_note_packet(b_data)
                    if verbosity >= 1:
                        logging.info("Note")
                        print(b_data)
                else:
                    raise ValueError(
                        f"ERROR in packet ! Unknown tcp_data_type: {packet_type}"
                    )
            else:
                raise ValueError("ERROR: Wrong header. Skipping data")

    finally:
        # Clean up the connection
        if connection is not None:
            if verbosity >= 1:
                logging.info("Closing the connection")
            connection.close()
        sock.close()
