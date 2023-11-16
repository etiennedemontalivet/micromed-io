"""Micromed IO module"""

from datetime import datetime
from typing import List
import logging
import numpy as np
from micromed_io.header import ElectrodeReferences, MicromedHeader


class MicromedIO:
    """Micromed IO class

    This class provides the basics for decoding Micromed data. It is common between files and
    TCP communication.

    Parameters
    ----------
    picks : List[str], default=None
        Channels to pick from EEGs data (all channels are stored). Channel names must follow
        the same format as in SystemPLUS Evolution (see EEG Setup Montage). WARNING: see Note 3.
        Example : ["Fp1-G2", "Fpz-G2", "MKR+-MKR-"]
        If None, all channels are included. The default is None.

    Attributes
    ----------
    micromed_header: MicromedHeader
        The corresponding micromed header of this connection.
    current_data_eeg: np.ndarray
        The current eeg data of shape (nb_of_channels, nb_of_samples).
    picks : List[str]
        Channels to pick from EEGs data (all channels are sent via TCP). Channel names follow
        the same format as in SystemPLUS Evolution (see EEG Setup Montage). WARNING: This impact
        the channels order.
        Example : ["Fp1-G2", "Fpz-G2", "MKR+-MKR-"]
    picks_id : np.array
        Indexes of the channels to pick.


    See also
    --------
    micromed_io.header.MicromedHeader

    """

    def __init__(
        self,
        picks: List[str] = None,
    ):
        self.micromed_header = MicromedHeader()
        self.current_data_eeg = None
        self.picks = picks
        self.picks_id = None
        self.epoch_buffer = None
        self.mkr_index = None  # index of MKR+-MKR- channel in micromed_header.ch_names
        self.current_channels = None
        self.notes = {}
        self.note_start_offset = -1

    def decode_data_header_packet(self, packet: bytearray):
        """Decode most of the micromed header data packet.
        TODO: include markers

        Parameters
        ----------
        packet : bytearray
            The header packet to decode.

        Raises
        ------
        ValueError
            If any "fixCode" sent by Micromed is not corresponding (LABCOD, ORDER,...)
            cf detailed documentation.

        """

        self.micromed_header.surname = packet[64 : (64 + 22)].decode().strip("\x00")
        self.micromed_header.name = packet[86 : (86 + 20)].decode().strip("\x00")
        self.micromed_header.acq_unit = int.from_bytes(packet[134:136], "little")
        self.micromed_header.nb_of_channels = int.from_bytes(packet[142:144], "little")
        self.micromed_header.min_sampling_rate = int.from_bytes(
            packet[146:148], "little"
        )
        self.micromed_header.recording_date = datetime(
            day=int.from_bytes(packet[128:129], "little"),
            month=int.from_bytes(packet[129:130], "little"),
            year=int.from_bytes(packet[130:131], "little") + 1900,
            hour=int.from_bytes(packet[131:132], "little"),
            minute=int.from_bytes(packet[132:133], "little"),
            second=int.from_bytes(packet[133:134], "little"),
        )
        self.micromed_header.data_address = int.from_bytes(packet[138:142], "little")
        self.micromed_header.nb_of_bytes = int.from_bytes(packet[148:150], "little")
        self.micromed_header.header_type = int.from_bytes(packet[175:176], "little")

        # Check micromed header type (must be 4)
        if self.micromed_header.header_type != 4:
            raise ValueError(
                f"Error: Header is not 4 but {self.micromed_header.header_type}. "
                + "Parsing is inappropriate."
            )

        # Retrieve stored channels ID
        if packet[176 : 176 + 8].decode("utf-8").strip() != "ORDER":
            raise ValueError(
                f"[MICROMED IO] Error: {packet[176 : 176 + 8]} must be equal to 'ORDER'"
            )
        code_start_offset = int.from_bytes(packet[184:188], "little")
        self.micromed_header.stored_channels = []
        for iCh in range(self.micromed_header.nb_of_channels):
            self.micromed_header.stored_channels.append(
                int.from_bytes(
                    packet[
                        code_start_offset + 2 * iCh : code_start_offset + 2 * (iCh + 1)
                    ],
                    "little",
                )
            )

        # Retrieve stored channels name
        if packet[192 : 192 + 8].decode("utf-8").strip() != "LABCOD":
            raise ValueError(
                f"[MICROMED TCP] Error: {packet[192 : 192 + 8].decode()} must be equal to 'LABCOD'"
            )
        elec_start_offset = int.from_bytes(packet[200:204], "little")
        self.micromed_header.ch_names = []
        for iCh in self.micromed_header.stored_channels:
            pos_elec = (
                packet[
                    elec_start_offset
                    + 128 * iCh
                    + 2 : elec_start_offset
                    + 128 * iCh
                    + 2
                    + 6
                ]
                .decode("utf-8")
                .strip("\x00")
            )
            neg_elec = (
                packet[
                    elec_start_offset
                    + 128 * iCh
                    + 8 : elec_start_offset
                    + 128 * iCh
                    + 8
                    + 6
                ]
                .decode("utf-8")
                .strip("\x00")
            )
            self.micromed_header.ch_names.append(f"{pos_elec}-{neg_elec}")

        # Retrieve note area
        if packet[208 : 208 + 8].decode("utf-8").strip() != "NOTE":
            raise ValueError(
                f"[MICROMED IO] Error: {packet[208 : 208 + 8].decode()} must be equal to 'NOTE'"
            )
        self.micromed_header.note_address = int.from_bytes(packet[216:220], "little")

        # construct the indexes of channels to pick in epoch buffer
        if self.picks is None:
            self.picks_id = np.arange(len(self.micromed_header.stored_channels))
        else:
            # Check that all channels are pickable
            for ch in self.picks:
                if ch not in self.micromed_header.ch_names:
                    raise ValueError(
                        f"[MICROMED IO] {ch} is not in "
                        + f"{self.micromed_header.ch_names}. Please fix it in config.ini file."
                    )
            self.picks_id = np.array(
                [self.micromed_header.ch_names.index(ch) for ch in self.picks],
                dtype=int,
            )

        # Extract electrode references for conversion purpose
        self.micromed_header.elec_refs = []
        for iCh in self.micromed_header.stored_channels:
            refs = ElectrodeReferences()
            start = elec_start_offset + 128 * iCh + 14
            refs.logic_min = int.from_bytes(
                packet[start : start + 4], "little", signed=True
            )
            refs.logic_max = int.from_bytes(
                packet[start + 4 : start + 8], "little", signed=True
            )
            refs.logic_ground = int.from_bytes(
                packet[start + 8 : start + 12], "little", signed=True
            )
            refs.phy_min = int.from_bytes(
                packet[start + 12 : start + 16], "little", signed=True
            )
            refs.phy_max = int.from_bytes(
                packet[start + 16 : start + 20], "little", signed=True
            )
            refs.units = int.from_bytes(
                packet[start + 20 : start + 22], "little", signed=True
            )
            self.micromed_header.elec_refs.append(refs)

    def decode_operator_note_packet(self, note_packet: bytearray):
        """Decode the operator notes

        Parameters
        ----------
        note_packet : bytearray
            The packet to decode. It must start at the note area.
        """
        for iNote in range(200):  # 200 = MAX_NOTE
            sample = int.from_bytes(note_packet[44 * iNote : 44 * iNote + 4], "little")
            comment = (
                note_packet[44 * iNote + 4 : 44 * (iNote + 1)]
                .decode("utf-8")
                .strip("\x00")
            )
            if sample == 0:  # that means no note anymore. cf Micromed doc
                break
            self.notes[sample] = comment

    # pylint: disable=too-many-branches,too-many-statements
    def decode_data_eeg_packet(
        self,
        packet: bytearray,
        picks: List = None,
        keep_raw: bool = False,
        use_volt: bool = False,
    ) -> bool:
        """Decode eeg data packet.
        Conversion is made to get physiological value of eegs.

        Parameters
        ----------
        packet : bytearray
            The EEGs data packet to decode.
        picks : List, optional
            A list of channel to extract. If None, all channels are extracted.
            The default is None.
        keep_raw : bool, optional
            If True, the data won't be converted to voltage. The default is False.
        use_volt : bool, optional
            If True, the data is scaled to Volts. If False, whatever unit is used by Micromed.
            Note that you may loose resolution by doing that. The default is False.

        Returns
        -------
        bool
            False if decoding is suspicious/wrong.

        Raises
        ------
        ValueError
            If data is not encoded on 1,2 or 4 bytes. Should not happen.

        Notes
        -----
        EEGs data are stored in this order (per packet):
        ``Ch1_t0, Ch2_t0, ... ChN_t0, Ch1_t1, Ch2_t1, ... ChN_t1, ...``

        ``self.current_data_eeg`` is always ordered regarding the order of the channels
        in self.micromed_header.ch_names
        """

        packet_size = len(packet)
        n_bytes = self.micromed_header.nb_of_bytes
        nb_of_channels = self.micromed_header.nb_of_channels

        if picks is None:
            picks = self.micromed_header.ch_names

        if n_bytes in [1, 2]:
            dt = np.dtype(np.uint16, "little")
        elif n_bytes == 4:
            dt = np.dtype(np.int32, "little")
        else:
            raise ValueError(f"Error: code not yet implemented for n_bytes={n_bytes}.")

        # MKR+MKR- is used to double check extraction/parsing of data
        # if it is not in picks, we add it temporary
        orig_picks = picks.copy()
        mkr_channels = [ch for ch in self.micromed_header.ch_names if "MKR" in ch]
        for ch in mkr_channels:
            if ch not in picks:
                picks.append(ch)

        raw_values = np.frombuffer(packet, dtype=dt)
        nb_of_samples = int(packet_size // n_bytes // nb_of_channels)

        reshaped_data = []
        t = np.arange(nb_of_samples) * nb_of_channels
        for i in range(nb_of_channels):
            if self.micromed_header.ch_names[i] in picks:
                if keep_raw is True:
                    reshaped_data.append(np.take(raw_values, t + i))
                else:
                    logic_min = self.micromed_header.elec_refs[i].logic_min
                    logic_max = self.micromed_header.elec_refs[i].logic_max
                    logic_ground = self.micromed_header.elec_refs[i].logic_ground
                    phy_min = self.micromed_header.elec_refs[i].phy_min
                    phy_max = self.micromed_header.elec_refs[i].phy_max
                    loc = (phy_max - phy_min) / (logic_max - logic_min + 1)
                    if use_volt is True:
                        unit = self.micromed_header.elec_refs[i].units
                        ratio = 0
                        if unit == -1:
                            ratio = 1e-9
                        elif unit == 0:
                            ratio = 1e-6
                        elif unit == 1:
                            ratio = 1e-3
                        elif unit == 2:
                            ratio = 1
                        else:
                            raise ValueError(
                                f"Cannot convert data to Volts. unit is inappropriate: {unit}."
                            )
                        loc *= ratio
                    reshaped_data.append(
                        np.multiply(
                            np.subtract(
                                np.take(raw_values, t + i).astype(int), logic_ground
                            ),
                            loc,
                        )
                    )

        self.current_data_eeg = np.array(reshaped_data)
        self.current_channels = picks
        if keep_raw is True:
            is_well_extracted = True
        else:
            is_well_extracted = self._check_eegs_data(mkr_channels)

        for ch in mkr_channels:
            if ch not in orig_picks:
                self.current_data_eeg = np.delete(
                    self.current_data_eeg,
                    (self.current_channels.index(ch)),
                    axis=0,
                )
                self.current_channels.remove(ch)

        return is_well_extracted

    def _check_eegs_data(self, mkr_channels) -> bool:
        """Check that eegs data are not corrupted

        Returns
        -------
        bool
            True if MKR+-MKR- channel absolute values are close to 50 (µV). Else False.
        """
        success = True
        for ch in mkr_channels:
            if not all(
                np.isclose(
                    abs(self.current_data_eeg[self.current_channels.index(ch)]), 50
                )
            ):
                success = False
        if not success:
            logging.warning("MKR channel(s) is not close to 50mV")

        return success
