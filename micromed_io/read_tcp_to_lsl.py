"""
Read data sent by Micromed through TCP.
"""
import logging
import socket
from datetime import datetime

import click
import numpy as np
import pylsl

from micromed_io.in_out import MicromedHeader, MicromedIO
from micromed_io.tcp import MicromedPacketType, decode_tcp_header_packet


def recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data


def init_lsl(
    header: MicromedHeader,
    lsl_name: str = "Micromed",
    lsl_type: str = "EEG",
    lsl_source_id: str = "micromed_eeg",
) -> pylsl.StreamOutlet:
    """Initializes the Labstreaming Layer outlet with the Micromed Header information"""
    # data outlet
    info = pylsl.StreamInfo(
        name=lsl_name,
        type=lsl_type,
        channel_count=int(header.nb_of_channels),
        nominal_srate=int(header.min_sampling_rate),
        channel_format="float32",
        source_id=lsl_source_id,
    )

    info.desc().append_child_value("manufacturer", "Micromed")
    channels = info.desc().append_child("channels")
    for _, ch_name in enumerate(header.ch_names):
        channels.append_child("channel").append_child_value(
            "label", ch_name
        ).append_child_value("unit", "microvolts").append_child_value("type", "EEG")

    # ready to parse
    logging.info("Micromed LSL server ready.")
    return pylsl.StreamOutlet(info)


@click.command(context_settings=dict(max_content_width=120))
@click.option(
    "--address",
    "-a",
    default="localhost",
    type=str,
    required=False,
    help="the TCP address to connect to",
    show_default=True,
)
@click.option(
    "--port",
    "-p",
    default=5123,
    type=int,
    required=False,
    help="The TCP port number to connect to",
    show_default=True,
)
@click.option(
    "--verbosity",
    "-v",
    default="1",
    type=click.Choice(["0", "1", "2"]),
    required=False,
    help="Increase output verbosity",
    show_default=True,
)
@click.option(
    "--lsl-name",
    "-ln",
    default="Micromed",
    type=str,
    required=False,
    help="the LSL stream name",
    show_default=True,
)
@click.option(
    "--lsl-type",
    "-lt",
    default="EEG",
    type=str,
    required=False,
    help="the LSL stream type",
    show_default=True,
)
@click.option(
    "--lsl-source-id",
    "-lsi",
    default="micromed_eeg",
    type=str,
    required=False,
    help="the LSL stream source id",
    show_default=True,
)
def run(
    address: str = "localhost",
    port: int = 5123,
    lsl_name: str = "Micromed",
    lsl_type: str = "EEG",
    lsl_source_id: str = "micromed_eeg",
    verbosity: int = 1,
) -> None:
    logging.basicConfig(level=0, format=("%(asctime)s\t\t%(levelname)s\t\t%(message)s"))
    verbosity = int(verbosity)  # because of click choice...
    previous_eeg_packet_time = datetime.now()

    while True:
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Bind the socket to the port
        server_address = (address, port)
        if verbosity >= 1:
            logging.info("starting up on %s port %s" % server_address)
        sock.bind(server_address)
        sock.listen(1)

        sock.settimeout(5)
        DONE = False
        connection = None

        logging.info("Waiting for a connection...")
        while connection is None:
            # Wait for a connection
            try:
                connection, _ = sock.accept()
                if verbosity >= 1:
                    logging.info("Connection from %s port %s" % server_address)
            except Exception as e:
                logging.warning(e)

        sock.settimeout(None)

        lsl_outlet = None
        # create micromed
        micromed_io = MicromedIO()
        try:
            while True:
                header = connection.recv(10)  # 10 is enoughbut more is fine too
                b_header = bytearray(header)
                packet_type, next_packet_size = decode_tcp_header_packet(b_header)

                if packet_type is not None:
                    data = recvall(connection, next_packet_size)
                    b_data = bytearray(data)

                    if packet_type == MicromedPacketType.HEADER:
                        micromed_io.decode_data_header_packet(b_data)

                        logging.info("Got Micromed header. Init LSL stream...")
                        if verbosity >= 1:
                            logging.debug(
                                f"n_channels={micromed_io.micromed_header.nb_of_channels}, "
                                + f"sfreq={micromed_io.sfreq}, "
                                + f"first 10 ch_names: {micromed_io.micromed_header.ch_names[:10]}"
                            )
                        lsl_outlet = init_lsl(
                            micromed_io.micromed_header,
                            lsl_name=lsl_name,
                            lsl_type=lsl_type,
                            lsl_source_id=lsl_source_id,
                        )

                    elif packet_type == MicromedPacketType.EEG_DATA:
                        if not micromed_io.decode_data_eeg_packet(b_data):
                            logging.error("Error in EEG data packet")

                        if verbosity >= 2:
                            logging.info(
                                f"Received EEG data: {micromed_io.current_data_eeg}"
                            )

                        if lsl_outlet is not None:
                            if (
                                verbosity >= 1
                                and (
                                    datetime.now() - previous_eeg_packet_time
                                ).total_seconds()
                                > 2
                            ):  # don't bother user too much - wait 2 sec between 2 logs
                                previous_eeg_packet_time = datetime.now()
                                logging.debug(
                                    f"Receiving TCP packet - LSL Sending chunk of size {micromed_io.current_data_eeg.T.shape}"
                                )
                            lsl_outlet.push_chunk(
                                np.ascontiguousarray(
                                    micromed_io.current_data_eeg.T.astype("float32")
                                )
                            )

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

        except Exception as e:
            logging.error(e)

        finally:
            # Clean up the connection
            if connection is not None:
                if verbosity >= 1:
                    logging.info("Closing the connection")
                connection.close()
            sock.close()


if __name__ == "__main__":
    run()
