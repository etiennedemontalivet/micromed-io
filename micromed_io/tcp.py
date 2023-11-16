"""Micromed TCP module."""

from enum import IntEnum
import sys

sys.path.append("..")
from micromed_io.in_out import MicromedIO
import logging


class MicromedPacketType(IntEnum):
    """Micromed packet type."""

    HEADER = 0
    EEG_DATA = 1
    NOTE = 2


def decode_tcp_header_packet(packet: bytearray):
    """Decode the Micromed tcp header packet.

    Parameters
    ----------
    packet : bytearray
        The tcp packet to decode.

    Returns
    -------
    bool
        True if decoding was successful. Else False.
    """
    packet_type = None
    next_packet_size = None
    if len(packet) > 0:
        # Check that the packet is not corrupted
        if packet[:4].decode() == "MICM":
            packet_type = int.from_bytes(packet[4:6], "little")
            next_packet_size = int.from_bytes(packet[6:10], "little")
        else:
            logging.warning(f"Wrong header packet: {packet.decode()}")
    else:
        logging.warning(f"header empty packet: [{packet.decode()}]")
    return packet_type, next_packet_size
