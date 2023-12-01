"""
Emulate from a TRC file Micromed sending data through TCP.

Note: The server must be launched before.

HOW TO USE:
> python emulate_trc_tcpip.py --help
> python emulate_trc_tcpip.py --file=../data/sample.TRC
"""
import logging
import socket
import numpy as np
import time
from datetime import datetime
from pathlib import Path
import click

from micromed_io.in_out import MicromedIO
import micromed_io.tcp as mmio_tcp


@click.command(context_settings=dict(max_content_width=120))
@click.option("--file", "-f", type=str, required=True, help="the TRC file to emulate")
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
    "--packet-time",
    "-pt",
    default=256,
    type=int,
    required=False,
    help="The time (in ms) of data to send",
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
def run(
    file: str,
    address: str = "localhost",
    port: int = 5123,
    packet_time: int = 256,
    verbosity: int = 1,
) -> None:
    """Emulate a Micromed TCP client based on a TRC file"""
    logging.basicConfig(
        level=0,
        format=(
            "[%(asctime)s - %(filename)s:%(lineno)d]\t\t%(levelname)s\t\t%(message)s"
        ),
    )
    verbosity = int(verbosity)  # because of click choice...
    # check if trc file exists
    if not Path(file).exists():
        raise FileNotFoundError(f"{file} does not exist")

    # open trc file
    with open(str(Path(file)), "rb") as f:
        b_data_trc = f.read()
    if verbosity >= 1:
        logging.info("TRC file read done.")

    # create Micromed
    micromed_io = MicromedIO()
    micromed_io.decode_data_header_packet(b_data_trc)
    markers = dict(
        sorted(micromed_io.micromed_header.markers.items())
    )  # ensure sorted samples
    notes = dict(
        sorted(micromed_io.micromed_header.notes.items())
    )  # ensure sorted samples

    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the port
    server_address = (address, port)
    if verbosity >= 1:
        logging.info("starting up on %s port %s" % server_address)
    is_not_connected = True

    while is_not_connected:
        try:
            sock.connect(server_address)
            is_not_connected = False
        except Exception as e:
            logging.warning(e)

    # some general variables
    sample_length = (
        micromed_io.micromed_header.nb_of_channels
        * micromed_io.micromed_header.nb_of_bytes
    )
    sfreq = micromed_io.micromed_header.min_sampling_rate
    n_samples_per_packet = int(packet_time * 1e-3 * sfreq)
    eeg_packet_length = sample_length * n_samples_per_packet
    header_address = micromed_io.micromed_header.data_address
    if verbosity >= 1:
        logging.info("Connected!")
        logging.info(
            f"got {len(b_data_trc[header_address:])} bytes - Sending {len(b_data_trc[header_address:]) // sample_length} samples for {len(b_data_trc[header_address:]) / (sample_length * sfreq)} sec"
        )

    # Send the Micromed header data
    tcp_header = mmio_tcp.get_tcp_header(
        mmio_tcp.MicromedPacketType.HEADER, header_address
    )
    if verbosity >= 1:
        logging.info("Sending Micromed header")
    sock.send(tcp_header)
    sock.send(b_data_trc[:header_address])  # send micromed header
    time.sleep(0.1)  # give time for the header to be sent

    start_time = datetime.now()
    current_data_sample = 0
    try:
        while True:
            if (current_data_sample + n_samples_per_packet) / sfreq <= (
                datetime.now() - start_time
            ).total_seconds():
                current_data_sample += n_samples_per_packet

                # check that we are on time
                if (current_data_sample + 5 * n_samples_per_packet) / sfreq <= (
                    datetime.now() - start_time
                ).total_seconds():
                    logging.error(
                        "Critical error: Running out of time. Please increase the packe_size so the emulator can send all the data on time."
                    )
                    return

                # SEND MARKER
                to_rm = []
                for marker_sample, marker_value in markers.items():
                    if marker_sample <= current_data_sample:
                        # send marker
                        if verbosity >= 1:
                            logging.info(f"Sending marker: {marker_value}")

                        tcp_header = mmio_tcp.get_tcp_header(
                            mmio_tcp.MicromedPacketType.MARKER, 6
                        )
                        sock.send(tcp_header)
                        sock.send(
                            mmio_tcp.encode_marker_packet(
                                marker_sample, np.uint16(marker_value)
                            )
                        )  # send micromed header
                        to_rm.append(marker_sample)
                    else:
                        # we can stop cause dict is sorted
                        # this is for time optimization
                        break
                # remove sent markers
                [markers.pop(k) for k in to_rm]

                # SEND NOTE_
                to_rm = []
                for note_sample, note_value in notes.items():
                    if note_sample <= current_data_sample:
                        # send marker
                        if verbosity >= 1:
                            logging.info(f"Sending note: {note_value}")

                        tcp_header = mmio_tcp.get_tcp_header(
                            mmio_tcp.MicromedPacketType.NOTE, 44
                        )
                        sock.send(tcp_header)
                        sock.send(mmio_tcp.encode_note_packet(note_sample, note_value))
                        to_rm.append(note_sample)
                    else:
                        # we can stop cause dict is sorted
                        # this is for time optimization
                        break
                # remove sent markers
                [notes.pop(k) for k in to_rm]

                # SEND DATA
                tcp_header = mmio_tcp.get_tcp_header(
                    mmio_tcp.MicromedPacketType.EEG_DATA, eeg_packet_length
                )
                sock.send(tcp_header)
                data_to_send = b_data_trc[
                    header_address
                    + current_data_sample * (sample_length) : header_address
                    + (current_data_sample + n_samples_per_packet) * sample_length
                ]
                sock.send(data_to_send)

                # debug only
                if verbosity == 2:
                    logging.info(
                        f"sending {len(data_to_send)}bytes with packet_len={eeg_packet_length}; current_ds={current_data_sample}; s={header_address}"
                    )

                # check if no more data
                if (
                    current_data_sample + n_samples_per_packet
                    >= len(b_data_trc[header_address:]) / sample_length
                ):
                    logging.info("TRC file over")
                    break

    except Exception as e:
        logging.error("exception catched: " + str(e))

    finally:
        # Clean up the connection
        logging.info("Closing the server")
        sock.close()


if __name__ == "__main__":
    run()
