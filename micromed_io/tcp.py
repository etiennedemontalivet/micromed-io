"""Micromed TCP module."""

import sys
from enum import IntEnum

sys.path.append("..")
import logging

from micromed_io.in_out import MicromedIO


class MicromedPacketType(IntEnum):
    """Micromed packet type."""

    HEADER = 0
    EEG_DATA = 1
    NOTE = 2
    MARKER = 3


def get_tcp_header(packet_type: MicromedPacketType, size: int) -> bytearray:
    """Build the Micromed TCP header

    Parameters
    ----------
    packet_type : MicromedPacketType
        The packet type to be sent
    size : int
        The size of the packet to be sent

    Returns
    -------
    bytearray
        The TCP header sent right before any packet
    """
    tcp_header = bytearray(b"MICM")
    tcp_header.extend((packet_type).to_bytes(2, byteorder="little"))
    tcp_header.extend(size.to_bytes(4, byteorder="little"))
    return tcp_header


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


def decode_tcp_marker_packet(packet: bytearray):
    """Decode the Micromed tcp markers packet.

    Parameters
    ----------
    packet : bytearray
        The tcp packet to decode.

    Returns
    -------
    tuple
        trigger_sample: the sample when the marker is received
        trigger_value: trigger value
    """
    trigger_sample = int.from_bytes(packet[:4], byteorder="little")
    trigger_value = int.from_bytes(packet[4:6], byteorder="little")
    return trigger_sample, trigger_value
