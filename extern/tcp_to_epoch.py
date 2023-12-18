"""
Read data sent by Micromed through TCP and store it into a buffer. Every
time the buffer is full, read the epoch and print it

How to use
==========

.. code:: bash

    $ python tcp_to_epoch.py --help
"""
import logging
import socket
from datetime import datetime
import click


import micromed_io.tcp as mmio_tcp
from micromed_io.buffer import MicromedBuffer


def recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data


@click.command(context_settings=dict(max_content_width=120))
@click.option(
    "--address",
    "-a",
    default="localhost",
    type=str,
    required=False,
    help="the TCP address to use for the server (your IP)",
    show_default=True,
)
@click.option(
    "--port",
    "-p",
    default=5123,
    type=int,
    required=False,
    help="The TCP port number to use",
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
    "--epoch-size",
    default=5.0,
    type=float,
    required=False,
    help="The epoch/window size in sec",
    show_default=True,
)
@click.option(
    "--overlap",
    default=2.5,
    type=float,
    required=False,
    help="The overlap between 2 successive epochs in sec",
    show_default=True,
)
def run(
    address: str = "localhost",
    port: int = 5123,
    epoch_size: float = 5.0,
    overlap: float = 2.5,
    verbosity: int = 1,
) -> None:
    """Read online TCP data from Micromed device and store it into a buffer. Every time the buffer is full, print it."""
    logging.basicConfig(
        level=0,
        format=(
            "[%(asctime)s - %(filename)s:%(lineno)d]\t\t%(levelname)s\t\t%(message)s"
        ),
    )

    verbosity = int(verbosity)  # because of click choice...

    while True:
        # Create a IPv4 based (AF_INET) TCP (SOCK_STREAM) connection
        # https://docs.python.org/3/library/socket.html#example
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Bind the socket to the port
        server_address = (address, port)
        if verbosity >= 1:
            logging.info("starting up on %s port %s" % server_address)
        sock.bind(server_address)
        sock.listen(1)

        sock.settimeout(5)
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

        # create micromed buffer
        micromed_buffer = MicromedBuffer(
            epoch_duration=epoch_size, epoch_overlap=overlap
        )
        previous_eeg_epoch_time = datetime.now()
        try:
            while True:
                header = connection.recv(10)  # 10 is enoughbut more is fine too
                b_header = bytearray(header)
                packet_type, next_packet_size = mmio_tcp.decode_tcp_header_packet(
                    b_header
                )

                if packet_type is not None:
                    data = recvall(connection, next_packet_size)
                    b_data = bytearray(data)

                    if packet_type == mmio_tcp.MicromedPacketType.HEADER:
                        micromed_buffer.decode_data_header_packet(b_data)

                        logging.info("Got Micromed header.")
                        if verbosity >= 1:
                            logging.debug(
                                f"n_channels={micromed_buffer.micromed_header.nb_of_channels}, "
                                + f"sfreq={micromed_buffer.sfreq}, "
                                + f"first 10 ch_names: {micromed_buffer.micromed_header.ch_names[:10]}"
                            )

                    elif packet_type == mmio_tcp.MicromedPacketType.EEG_DATA:
                        if not micromed_buffer.decode_data_eeg_packet(b_data):
                            logging.error(
                                "Error in EEG data packet. (You can drop this data or "
                                + "interpolate or whatever)"
                            )
                        if micromed_buffer.update_epoch_buffer():
                            logging.info(
                                f"Buffer of size {micromed_buffer.current_epoch.shape} "
                                + "is full: PROCESS HERE using the micromed_buffer.current_epoch."
                                + f" [delta time = {(datetime.now() - previous_eeg_epoch_time).total_seconds()}s]"
                            )
                            print(micromed_buffer.current_epoch)
                            previous_eeg_epoch_time = datetime.now()

                    elif packet_type == mmio_tcp.MicromedPacketType.NOTE:
                        note_sample, note_value = mmio_tcp.decode_tcp_note_packet(
                            b_data
                        )
                        if verbosity >= 1:
                            logging.info(
                                f"Received note: sample={note_sample} ,value={note_value}"
                            )

                    elif packet_type == mmio_tcp.MicromedPacketType.MARKER:
                        marker_sample, marker_value = mmio_tcp.decode_tcp_marker_packet(
                            b_data
                        )
                        if verbosity >= 1:
                            logging.info(
                                f"Received marker: sample={marker_sample} ,value={marker_value}"
                            )
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
