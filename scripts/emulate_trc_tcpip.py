"""
Emulate from a TRC file Micromed sending data through TCP.

Note: The server must be launched before.

HOW TO USE:
> python emulate_trc_tcpip.py --help
> python emulate_trc_tcpip.py --file=../data/sample.TRC
"""
import socket
import time
import logging
from pathlib import Path
import click

from micromed_io.in_out import MicromedIO


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
    "--packet_size",
    "-ps",
    default=64,
    type=int,
    required=False,
    help="The data tcp packet length",
    show_default=True,
)
@click.option(
    "--verbosity",
    "-v",
    default=1,
    type=click.Choice(["0", "1", "2"]),
    required=False,
    help="Increase output verbosity",
    show_default=True,
)
def run(file: str, address: str, port: int, packet_size: int, verbosity: int) -> None:
    """Emulate a Micromed TCP client based on a TRC file"""
    logging.basicConfig(level=0, format=("%(asctime)s\t\t%(levelname)s\t\t%(message)s"))
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
    data_length = (
        micromed_io.micromed_header.nb_of_channels
        * micromed_io.micromed_header.nb_of_bytes
        * packet_size
    )
    s = micromed_io.micromed_header.data_address
    if verbosity >= 1:
        logging.info("Connected!")
        logging.info(f"Sending {len(b_data_trc[s:]) // data_length} packets")

    # Time between 2 packets in sec
    trigger_time = packet_size / micromed_io.micromed_header.min_sampling_rate

    # Send the Micromed header data
    tcp_header = bytearray(b"MICM")
    tcp_header.extend((0).to_bytes(2, byteorder="little"))
    tcp_header.extend(s.to_bytes(4, byteorder="little"))
    if verbosity >= 1:
        logging.info("tcp header for header data")
        logging.info(tcp_header)
    sock.send(tcp_header)
    sock.send(b_data_trc[:s])  # send micromed header
    time.sleep(0.1)  # give time for the header to be sent

    starttime = time.time()
    for i in range(len(b_data_trc[s:]) // data_length):
        try:
            tcp_header = bytearray(b"MICM")
            tcp_header.extend((1).to_bytes(2, byteorder="little"))
            tcp_header.extend(data_length.to_bytes(4, byteorder="little"))
            sock.send(tcp_header)
            time.sleep(trigger_time / 10)
            sock.send(b_data_trc[s + i * (data_length) : s + (i + 1) * data_length])

        except Exception as e:
            logging.error("exception catched: " + str(e))
            break

        # debug only
        if verbosity == 2:
            logging.info(f"sending bytes")

        # wait before next packet
        time_to_sleep = trigger_time - ((time.time() - starttime) % trigger_time)
        if time_to_sleep > 0:
            time.sleep(time_to_sleep)
        else:
            logging.warning(
                f"WARNING: we are in the rush: time_to_seelp={time_to_sleep}."
                + "Increase packet size."
            )

    # Clean up the connection
    logging.info("Closing the server")
    sock.close()


if __name__ == "__main__":
    run()
