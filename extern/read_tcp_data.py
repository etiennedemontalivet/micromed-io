"""
Read data sent by Micromed through TCP.

HOW TO USE:
> python read_tcp_data.py --help
> python read_tcp_data.py
"""
import socket

import numpy as np

from micromed_io.in_out import MicromedIO
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
    micromed_io = MicromedIO()

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
                    micromed_io.decode_data_header_packet(b_data)
                    if verbosity >= 1:
                        logging.info("Micromed header")
                        print(micromed_io.micromed_header)

                elif packet_type == MicromedPacketType.EEG_DATA:
                    if not micromed_io.decode_data_eeg_packet(b_data):
                        logging.error("Error in EEG data packet")

                    if verbosity >= 1:
                        logging.info("Received EEG data")
                    if verbosity == 2:
                        print(micromed_io.current_data_eeg)

                elif packet_type == MicromedPacketType.NOTE:
                    # TODO: check tcp note parsing
                    micromed_io.decode_operator_note_packet(b_data)
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
