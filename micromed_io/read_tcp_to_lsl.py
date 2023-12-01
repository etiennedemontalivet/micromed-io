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
import micromed_io.tcp as mmio_tcp


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
    lsl_eeg_name: str = "Micromed",
    lsl_eeg_type: str = "EEG",
    lsl_eeg_source_id: str = "micromed_eeg",
    lsl_markers_name: str = "Micromed_Markers",
    lsl_markers_type: str = "Markers",
    lsl_markers_source_id: str = "micromed_markers",
    lsl_notes_name: str = "Micromed_Notes",
    lsl_notes_type: str = "Markers",
    lsl_notes_source_id: str = "micromed_notes",
) -> (pylsl.StreamOutlet, pylsl.StreamOutlet):
    """Initializes the Labstreaming Layer outlet with the Micromed Header information"""
    # data outlet
    info = pylsl.StreamInfo(
        name=lsl_eeg_name,
        type=lsl_eeg_type,
        channel_count=int(header.nb_of_channels),
        nominal_srate=int(header.min_sampling_rate),
        channel_format="float32",
        source_id=lsl_eeg_source_id,
    )

    # Create EEG data outlet
    info.desc().append_child_value("manufacturer", "Micromed")
    channels = info.desc().append_child("channels")
    for _, ch_name in enumerate(header.ch_names):
        channels.append_child("channel").append_child_value(
            "label", ch_name
        ).append_child_value("unit", "microvolts").append_child_value("type", "EEG")
    eeg_outlet = pylsl.StreamOutlet(info)

    # Create MARKERS outlet
    info_markers = pylsl.StreamInfo(
        name=lsl_markers_name,
        type=lsl_markers_type,
        channel_count=2,  # TODO: proper doc - [sample, value]
        nominal_srate=0,
        channel_format="int32",
        source_id=lsl_markers_source_id,
    )
    info_markers.desc().append_child_value("manufacturer", "Micromed_markers")
    channels = info_markers.desc().append_child("channels")
    for label in ["marker_sample", "marker_value"]:
        ch = channels.append_child("channel")
        ch.append_child_value("label", label)
        ch.append_child_value("type", "Marker")
    markers_outlet = pylsl.StreamOutlet(info_markers)

    # Create NOTES outlet
    info_notes = pylsl.StreamInfo(
        name=lsl_notes_name,
        type=lsl_notes_type,
        channel_count=2,  # TODO: proper doc - [sample, value]
        nominal_srate=0,
        channel_format="string",
        source_id=lsl_notes_source_id,
    )
    info_notes.desc().append_child_value("manufacturer", "Micromed_notes")
    channels = info_notes.desc().append_child("channels")
    for label in ["note_sample", "note_value"]:
        ch = channels.append_child("channel")
        ch.append_child_value("label", label)
        ch.append_child_value("type", "Marker")
    notes_outlet = pylsl.StreamOutlet(info_notes)

    # ready to parse
    logging.info("LSL server ready.")

    return eeg_outlet, markers_outlet, notes_outlet


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
    "--lsl-eeg-name",
    default="Micromed",
    type=str,
    required=False,
    help="the LSL stream name for the eeg",
    show_default=True,
)
@click.option(
    "--lsl-eeg-type",
    default="EEG",
    type=str,
    required=False,
    help="the LSL stream type for the eeg",
    show_default=True,
)
@click.option(
    "--lsl-eeg-source-id",
    default="micromed_eeg",
    type=str,
    required=False,
    help="the LSL stream source id for the eeg",
    show_default=True,
)
@click.option(
    "--lsl-markers-name",
    default="Micromed_Markers",
    type=str,
    required=False,
    help="the LSL stream name for the markers",
    show_default=True,
)
@click.option(
    "--lsl-markers-type",
    default="Markers",
    type=str,
    required=False,
    help="the LSL stream type for the markers",
    show_default=True,
)
@click.option(
    "--lsl-markers-source-id",
    default="micromed_marker",
    type=str,
    required=False,
    help="the LSL stream source id for the markers",
    show_default=True,
)
@click.option(
    "--lsl-notes-name",
    default="Micromed_Notes",
    type=str,
    required=False,
    help="the LSL stream name for the notes",
    show_default=True,
)
@click.option(
    "--lsl-notes-type",
    default="Markers",
    type=str,
    required=False,
    help="the LSL stream type for the notes",
    show_default=True,
)
@click.option(
    "--lsl-notes-source-id",
    default="micromed_notes",
    type=str,
    required=False,
    help="the LSL stream source id for the notes",
    show_default=True,
)
def run(
    address: str = "localhost",
    port: int = 5123,
    lsl_eeg_name: str = "Micromed",
    lsl_eeg_type: str = "EEG",
    lsl_eeg_source_id: str = "micromed_eeg",
    lsl_markers_name: str = "Micromed_Markers",
    lsl_markers_type: str = "Markers",
    lsl_markers_source_id: str = "micromed_markers",
    lsl_notes_name: str = "Micromed_Notes",
    lsl_notes_type: str = "Markers",
    lsl_notes_source_id: str = "micromed_notes",
    verbosity: int = 1,
) -> None:
    logging.basicConfig(
        level=0,
        format=(
            "[%(asctime)s - %(filename)s:%(lineno)d]\t\t%(levelname)s\t\t%(message)s"
        ),
    )

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

        lsl_eeg_outlet = None
        lsl_markers_outlet = None
        # create micromed
        micromed_io = MicromedIO()
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
                        micromed_io.decode_data_header_packet(b_data)

                        logging.info("Got Micromed header. Init LSL stream...")
                        if verbosity >= 1:
                            logging.debug(
                                f"n_channels={micromed_io.micromed_header.nb_of_channels}, "
                                + f"sfreq={micromed_io.sfreq}, "
                                + f"first 10 ch_names: {micromed_io.micromed_header.ch_names[:10]}"
                            )
                        lsl_eeg_outlet, lsl_markers_outlet, lsl_notes_outlet = init_lsl(
                            micromed_io.micromed_header,
                            lsl_eeg_name=lsl_eeg_name,
                            lsl_eeg_type=lsl_eeg_type,
                            lsl_eeg_source_id=lsl_eeg_source_id,
                            lsl_markers_name=lsl_markers_name,
                            lsl_markers_type=lsl_markers_type,
                            lsl_markers_source_id=lsl_markers_source_id,
                            lsl_notes_name=lsl_notes_name,
                            lsl_notes_type=lsl_notes_type,
                            lsl_notes_source_id=lsl_notes_source_id,
                        )

                    elif packet_type == mmio_tcp.MicromedPacketType.EEG_DATA:
                        if not micromed_io.decode_data_eeg_packet(b_data):
                            logging.error("Error in EEG data packet")
                        # log only
                        if verbosity >= 2:
                            logging.info(
                                f"Received EEG data: {micromed_io.current_data_eeg}"
                            )
                        # forward to lsl
                        if lsl_eeg_outlet is not None:
                            # log only
                            if (
                                verbosity >= 1
                                and (
                                    datetime.now() - previous_eeg_packet_time
                                ).total_seconds()
                                > 1
                            ):  # don't bother user too much - wait 2 sec between 2 logs
                                previous_eeg_packet_time = datetime.now()
                                logging.debug(
                                    f"Receiving TCP packet - LSL Sending chunk of size {micromed_io.current_data_eeg.T.shape}"
                                )
                            # send to lsl
                            lsl_eeg_outlet.push_chunk(
                                np.ascontiguousarray(
                                    micromed_io.current_data_eeg.T.astype("float32")
                                )
                            )

                    elif packet_type == mmio_tcp.MicromedPacketType.NOTE:
                        note_sample, note_value = mmio_tcp.decode_tcp_note_packet(
                            b_data
                        )
                        lsl_notes_outlet.push_sample([str(note_sample), note_value])
                        if verbosity >= 1:
                            logging.info(
                                f"Received note: sample={note_sample} ,value={note_value}"
                            )

                    elif packet_type == mmio_tcp.MicromedPacketType.MARKER:
                        marker_sample, marker_value = mmio_tcp.decode_tcp_marker_packet(
                            b_data
                        )
                        lsl_markers_outlet.push_sample([marker_sample, marker_value])
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
