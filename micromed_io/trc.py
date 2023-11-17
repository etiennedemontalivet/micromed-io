"""Micromed IO module
"""

from typing import List
from typing import Union
from pathlib import Path
import logging
import numpy as np

from micromed_io.in_out import MicromedIO


class MicromedTRC(MicromedIO):
    # pylint: disable=line-too-long
    """Micromed TRC class

    This class deals with Micromed TRC file

    Parameters
    ----------
    filename: str or Path
        The TRC filename.

    Attributes
    ----------
    filename: str or Path
        The TRC filename.

    """

    def __init__(
        self,
        filename: Union[str, Path],
    ):
        MicromedIO.__init__(self, None)
        self.filename = filename
        with open(self.filename, "rb") as f:
            b_data = f.read(
                self._get_data_address()
            )  # trick to not open the whole file
            self.decode_data_header_packet(b_data)

    def _get_data_address(self):
        """Read and return data address"""
        with open(self.filename, "rb") as f:
            packet = f.read(142)
            data_address = int.from_bytes(packet[138:142], "little")
        return data_address

    def get_header(self):
        """Get the header"""
        return self.micromed_header

    def get_sfreq(self):
        """Get the sampling frequency"""
        return self.sfreq

    def get_notes(self):
        """Get the notes"""
        return self.micromed_header.notes

    def get_markers(self):
        """Get the markers"""
        return self.micromed_header.markers

    def get_data(
        self, picks: List = None, keep_raw: bool = False, use_volt: bool = False
    ):
        """Get channels data in format (n_channels, n_sample)

        Parameters
        ----------
        picks : List, optional
            A list of channel to extract. If None, all channels are extracted.
            The default is None.
        keep_raw : bool, optional
            If True, the data won't be converted to voltage. The default is False.
        use_volt : bool, optional
            If True, the data is scaled to Volts. If False, whatever unit is used by Micromed.
            Note that you may loose resolution by doing that. The default is False.
        """
        with open(self.filename, "rb") as f:
            f.seek(self._get_data_address())
            b_data = f.read()
            self.decode_data_eeg_packet(b_data, picks, keep_raw, use_volt)
        return self.current_data_eeg
