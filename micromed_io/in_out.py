"""Micromed IO module"""

#
# the header parser has been updated to read almost all data thanks to wonambi library:
# https://wonambi-python.github.io/api/wonambi.ioeeg.micromed.html
#

import logging
from datetime import date, datetime
from struct import unpack
from typing import List

import numpy as np
from numpy import dtype

from micromed_io.header import ElectrodeReferences, MicromedHeader

N_ZONES = 15
MAX_SAMPLE = 128
MAX_CAN_VIEW = 128
ENCODING = "iso-8859-1"


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
    sfreq : float
        The sampling frequency


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
        self.mkr_index = None  # index of MKR+-MKR- channel in micromed_header.ch_names
        self.current_channels = None
        self.notes = {}
        self.note_start_offset = -1
        self.sfreq = None

    def decode_data_header_packet(self, packet: bytearray) -> None:
        """Decode all (but histories) of the micromed header data packet.

        Parameters
        ----------
        packet : bytearray
            The header packet to decode.

        """
        self._header = _read_header(packet)
        self.micromed_header.surname = self._header["surname"]
        self.micromed_header.name = self._header["name"]
        self.micromed_header.nb_of_channels = self._header["n_chan"]
        self.micromed_header.order = self._header["order"]
        self.micromed_header.acq_unit = self._header["acquisition_unit"]
        self.micromed_header.min_sampling_rate = self._header["s_freq"]
        self.micromed_header.nb_of_bytes = self._header["n_bytes"]
        self.micromed_header.header_type = self._header["header_type"]
        self.micromed_header.stored_channels = self._header["order"]
        self.micromed_header.ch_names = [
            f"{d['chan_name']}-{d['ground']}" for d in self._header["chans"]
        ]

        # construct the indexes of channels to pick
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

        # elec_refs is a list of electrode references. Dim 2 is
        # [logic_min, logic_max, logic_ground, phy_min, phy_max, units]
        self.micromed_header.elec_refs = [
            ElectrodeReferences(
                factor=d["factor"],
                logic_ground=d["logical_ground"],
                units=d["units"],
            )
            for d in self._header["chans"]
        ]
        self.micromed_header.data_address = self._header["BOData"]
        self.micromed_header.recording_date = self._header["start_time"]
        self.sfreq = self.micromed_header.min_sampling_rate
        # Handle notes
        notes_dict = {}
        for note_sample, note_val in self._header["notes"]:
            if note_sample == 0:
                break
            notes_dict[note_sample] = note_val.decode(ENCODING)
        self.micromed_header.notes = notes_dict

        # Handle notes
        markers_dict = {}
        for marker_sample, marker_val in self._header["trigger"]:
            if marker_sample == 4294967295 and marker_val == 65535:
                break
            markers_dict[marker_sample] = str(marker_val)
        self.micromed_header.markers = markers_dict

    # pylint: disable=too-many-branches,too-many-statements
    def decode_data_eeg_packet(
        self,
        packet: bytearray,
        picks: List = None,
        keep_raw: bool = False,
        use_volt: bool = False,
        check_data: bool = True,
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
        check_data: bool, optional
            Check if MKR channel(s) is close to 50mV. If not, return False. You can disable
            for speed performances.

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

        If a marker is sent through serial port, MKR channel(s) is not close to 50mV. The warning should
        then be ignored.
        """

        packet_size = len(packet)
        n_bytes = self.micromed_header.nb_of_bytes
        nb_of_channels = self.micromed_header.nb_of_channels
        is_well_extracted = True

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
        if check_data is True:
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
                    factor = self.micromed_header.elec_refs[i].factor
                    logic_ground = self.micromed_header.elec_refs[i].logic_ground

                    if use_volt is True:
                        unit = self.micromed_header.elec_refs[i].units
                        ratio = 0
                        if unit == "nV":
                            ratio = 1e-9
                        elif unit == "μV":
                            ratio = 1e-6
                        elif unit == "mV":
                            ratio = 1e-3
                        elif unit == "V":
                            ratio = 1
                        else:
                            raise ValueError(
                                f"Cannot convert data to Volts. unit is inappropriate: {unit}."
                            )
                        factor *= ratio
                    reshaped_data.append(
                        np.multiply(
                            np.subtract(
                                np.take(raw_values, t + i).astype(int),
                                logic_ground,
                            ),
                            factor,
                        )
                    )

        self.current_data_eeg = np.array(reshaped_data)
        self.current_channels = picks

        # check data and remove mkr channels if not selected
        if check_data is True:
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
            True if MKR+-MKR- channel absolute values are close to 50 (mV). Else False.
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
            logging.warning(
                "MKR channel(s) is not close to 50mV. If no trigger received, then data are corrupted."
            )

        return success


def _read_header(f):
    i_b = 0  # where
    orig = {}

    orig["title"] = f[:32].decode(ENCODING).strip()
    i_b += 32
    orig["laboratory"] = f[i_b : i_b + 32].strip(b"\x00").decode(ENCODING).strip()
    i_b += 32

    # patient
    orig["surname"] = f[i_b : i_b + 22].decode(ENCODING).strip()
    i_b += 22
    orig["name"] = f[i_b : i_b + 20].decode(ENCODING).strip()
    i_b += 20
    month, day, year = unpack("bbb", f[i_b : i_b + 3])
    i_b += 3
    try:
        orig["date_of_birth"] = date(year + 1900, month, day)
    except ValueError:
        orig["date_of_birth"] = None
    i_b += 19

    # recording
    day, month, year, hour, minute, sec = unpack("bbbbbb", f[i_b : i_b + 6])
    i_b += 6
    orig["start_time"] = datetime(year + 1900, month, day, hour, minute, sec)

    acquisition_unit_code = unpack("h", f[i_b : i_b + 2])[0]
    i_b += 2
    orig["acquisition_unit"] = ACQUISITION_UNIT.get(
        acquisition_unit_code, str(acquisition_unit_code)
    )
    filetype_code = unpack("H", f[i_b : i_b + 2])[0]
    i_b += 2
    orig["filetype"] = FILETYPE.get(filetype_code, "unknown headbox")

    orig["BOData"] = unpack("I", f[i_b : i_b + 4])[0]
    i_b += 4
    orig["n_chan"] = unpack("H", f[i_b : i_b + 2])[0]
    i_b += 2
    orig["multiplexer"] = unpack("H", f[i_b : i_b + 2])[0]
    i_b += 2
    orig["s_freq"] = unpack("H", f[i_b : i_b + 2])[0]
    i_b += 2
    orig["n_bytes"] = unpack("H", f[i_b : i_b + 2])[0]
    i_b += 2
    orig["compression"] = unpack("H", f[i_b : i_b + 2])[0]
    i_b += 2  # 0 non compression, 1 compression.
    orig["n_montages"] = unpack("H", f[i_b : i_b + 2])[0]
    i_b += 2  # Montages : number of specific montages
    orig["dvideo_begin"] = unpack("I", f[i_b : i_b + 4])[0]
    i_b += 4  # Starting sample of digital video
    orig["mpeg_delay"] = unpack("H", f[i_b : i_b + 2])[0]
    i_b += 2  # Number of frames per hour of de-synchronization in MPEG acq

    i_b += 15
    header_type_code = unpack("b", f[i_b : i_b + 1])[0]
    i_b += 1
    orig["header_type"] = HEADER_TYPE[header_type_code]

    zones = {}
    for _ in range(N_ZONES):
        zname, pos, length = unpack("8sII", f[i_b : i_b + 16])
        i_b += 16
        zname = zname.decode(ENCODING).strip()
        zones[zname] = pos, length

    pos, length = zones["ORDER"]
    order = np.frombuffer(f[pos:], dtype="u2", count=orig["n_chan"])

    chans = _read_labcod(f, zones["LABCOD"], order)

    pos, length = zones["NOTE"]
    DTYPE = dtype([("sample", "u4"), ("text", "S40")])
    notes = np.frombuffer(f[pos:], dtype=DTYPE, count=int(length / DTYPE.itemsize))

    pos, length = zones["FLAGS"]
    DTYPE = dtype([("begin", "u4"), ("end", "u4")])
    flags = np.frombuffer(f[pos:], dtype=DTYPE, count=int(length / DTYPE.itemsize))

    pos, length = zones["TRONCA"]
    DTYPE = dtype([("time_in_samples", "u4"), ("sample", "u4")])
    segments = np.frombuffer(f[pos:], dtype=DTYPE, count=int(length / DTYPE.itemsize))

    # impedance
    DTYPE = dtype([("positive", "u1"), ("negative", "u1")])
    pos, length = zones["IMPED_B"]
    impedance_begin = np.frombuffer(
        f[pos:], dtype=DTYPE, count=int(length / DTYPE.itemsize)
    )

    pos, length = zones["IMPED_E"]
    impedance_end = np.frombuffer(
        f[pos:], dtype=DTYPE, count=int(length / DTYPE.itemsize)
    )

    montage = _read_montage(f, zones["MONTAGE"])

    # if average has been computed
    pos, length = zones["COMPRESS"]
    i_b = pos
    avg = {}
    avg["trace"], avg["file"], avg["prestim"], avg["poststim"], avg["type"] = unpack(
        "IIIII", f[i_b : i_b + 5 * 4]
    )
    i_b += 5 * 4
    avg["free"] = f[i_b : i_b + 108].strip(b"\x01\x00")
    i_b += 108

    # history = _read_history(f, zones["HISTORY"])

    pos, length = zones["DVIDEO"]
    i_b = pos
    DTYPE = dtype(
        [("delay", "i4"), ("duration", "u4"), ("file_ext", "u4"), ("empty", "u4")]
    )
    dvideo = np.frombuffer(f, dtype=DTYPE, count=int(length / DTYPE.itemsize))

    # events
    DTYPE = dtype([("code", "u4"), ("begin", "u4"), ("end", "u4")])
    pos, length = zones["EVENT A"]
    event_a = np.frombuffer(f[pos:], dtype=DTYPE, count=int(length / DTYPE.itemsize))

    pos, length = zones["EVENT B"]
    event_b = np.frombuffer(f[pos:], dtype=DTYPE, count=int(length / DTYPE.itemsize))

    pos, length = zones["TRIGGER"]
    DTYPE = dtype([("sample", "u4"), ("code", "u2")])
    trigger = np.frombuffer(f[pos:], dtype=DTYPE, count=int(length / DTYPE.itemsize))

    orig.update(
        {
            "order": order,
            "chans": chans,
            "notes": notes,
            "flags": flags,
            "segments": segments,
            "impedance_begin": impedance_begin,
            "impedance_end": impedance_end,
            "montage": montage,
            # "history": history,
            "dvideo": dvideo,
            "event_a": event_a,
            "event_b": event_b,
            "trigger": trigger,
        }
    )

    return orig


ACQUISITION_UNIT = {
    0: "BQ124 - 24 channels headbox, Internal Interface",
    2: "MS40 - Holter recorder",
    6: "BQ132S - 32 channels headbox, Internal Interface",
    7: "BQ124 - 24 channels headbox, BQ CARD Interface",
    8: "SAM32 - 32 channels headbox, BQ CARD Interface",
    9: "SAM25 - 25 channels headbox, BQ CARD Interface",
    10: "BQ132S R - 32 channels reverse headbox, Internal Interface",
    11: "SAM32 R - 32 channels reverse headbox, BQ CARD Interface",
    12: "SAM25 R - 25 channels reverse headbox, BQ CARD Interface",
    13: "SAM32 - 32 channels headbox, Internal Interface",
    14: "SAM25 - 25 channels headbox, Internal Interface",
    15: "SAM32 R - 32 channels reverse headbox, Internal Interface",
    16: "SAM25 R - 25 channels reverse headbox, Internal Interface",
    17: "SD - 32 channels headbox with jackbox, SD CARD Interface -- PCI Internal Interface",
    18: "SD128 - 128 channels headbox, SD CARD Interface -- PCI Internal Interface",
    19: "SD96 - 96 channels headbox, SD CARD Interface -- PCI Internal Interface",
    20: "SD64 - 64 channels headbox, SD CARD Interface -- PCI Internal Interface",
    21: "SD128c - 128 channels headbox with jackbox, SD CARD Interface -- PCI Internal Interface",
    22: "SD64c - 64 channels headbox with jackbox, SD CARD Interface -- PCI Internal Interface",
    23: "BQ132S - 32 channels headbox, PCI Internal Interface",
    24: "BQ132S R - 32 channels reverse headbox, PCI Internal Interface",
}

FILETYPE = {
    40: "C128 C.R., 128 EEG (headbox SD128 only)",
    42: "C84P C.R., 84 EEG, 44 poly (headbox SD128 only)",
    44: "C84 C.R., 84 EEG, 4 reference signals (named MKR,MKRB,MKRC,MKRD) (headbox SD128 only)",
    46: "C96 C.R., 96 EEG (headbox SD128 -- SD96 -- BQ123S(r))",
    48: "C63P C.R., 63 EEG, 33 poly",
    50: "C63 C.R., 63 EEG, 3 reference signals (named MKR,MKRB,MKRC)",
    52: "C64 C.R., 64 EEG",
    54: "C42P C.R., 42 EEG, 22 poly",
    56: "C42 C.R., 42 EEG, 2 reference signals (named MKR,MKRB)",
    58: "C32 C.R., 32 EEG",
    60: "C21P C.R., 21 EEG, 11 poly",
    62: "C21 C.R., 21 EEG, 1 reference signal (named MKR)",
    64: "C19P C.R., 19 EEG, variable poly",
    66: "C19 C.R., 19 EEG, 1 reference signal (named MKR)",
    68: "C12 C.R., 12 EEG",
    70: "C8P C.R., 8 EEG, variable poly",
    72: "C8 C.R., 8 EEG",
    74: "CFRE C.R., variable EEG, variable poly",
    76: "C25P C.R., 25 EEG (21 standard, 4 poly transformed to EEG channels), 7 poly -- headbox BQ132S(r) only",
    78: "C27P C.R., 27 EEG (21 standard, 6 poly transformed to EEG channels), 5 poly -- headbox BQ132S(r) only",
    80: "C24P C.R., 24 EEG (21 standard, 3 poly transformed to EEG channels), 8 poly -- headbox SAM32(r) only",
    82: "C25P C.R., 25 EEG (21 standard, 4 poly transformed to EEG channels), 7 poly -- headbox SD with headbox JB 21P",
    84: "C27P C.R., 27 EEG (21 standard, 6 poly transformed to EEG channels), 5 poly -- headbox SD with headbox JB 21P",
    86: "C31P C.R., 27 EEG (21 standard, 10 poly transformed to EEG channels), 1 poly -- headbox SD with headbox JB 21P6",
    100: "C26P C.R., 26 EEG, 6 poly (headbox SD, SD64c, SD128c with headbox JB Mini)",
    101: "C16P C.R., 16 EEG, 16 poly (headbox SD with headbox JB M12)",
    102: "C12P C.R., 12 EEG, 20 poly (headbox SD with headbox JB M12)",
    103: "32P 32 poly (headbox SD, SD64c, SD128c with headbox JB Bip)",
    120: "C48P C.R., 48 EEG, 16 poly (headbox SD64)",
    121: "C56P C.R., 56 EEG, 8 poly (headbox SD64)",
    122: "C24P C.R., 24 EEG, 8 poly (headbox SD64)",
    140: "C52P C.R., 52 EEG, 12 poly (headbox SD64c, SD128c with 2 headboxes JB Mini)",
    141: "64P 64 poly (headbox SD64c, SD128c with 2 headboxes JB Bip)",
    160: "C88P C.R., 88 EEG, 8 poly (headbox SD96)",
    161: "C80P C.R., 80 EEG, 16 poly (headbox SD96)",
    162: "C72P C.R., 72 EEG, 24 poly (headbox SD96)",
    180: "C120P C.R., 120 EEG, 8 poly (headbox SD128)",
    181: "C112P C.R., 112 EEG, 16 poly (headbox SD128)",
    182: "C104P C.R., 104 EEG, 24 poly (headbox SD128)",
    183: "C96P C.R., 96 EEG, 32 poly (headbox SD128)",
    200: "C122P C.R., 122 EEG, 6 poly (headbox SD128c with 4 headboxes JB Mini)",
    201: "C116P C.R., 116 EEG, 12 poly (headbox SD128c with 4 headboxes JB Mini)",
    202: "C110P C.R., 110 EEG, 18 poly (headbox SD128c with 4 headboxes JB Mini)",
    203: "C104P C.R., 104 EEG, 24 poly (headbox SD128c with 4 headboxes JB Mini)",
    204: "128P 128 poly (headbox SD128c with 4 headboxes JB Bip)",
    205: "96P 96 poly (headbox SD128c with 3 headboxes JB Bip)",
}

HEADER_TYPE = {
    0: 'Micromed "System 1" Header type',
    1: 'Micromed "System 1" Header type',
    2: 'Micromed "System 2" Header type',
    3: 'Micromed "System98" Header type',
    4: 'Micromed "System98" Header type',
}

UNITS = {
    -1: "nV",
    0: "μV",
    1: "mV",
    2: "V",
    100: "%",
    101: "bpm",
    102: "dimentionless",
}


def _read_labcod(f, zone, order):
    pos, length = zone
    CHAN_LENGTH = 128

    chans = []

    for i_ch in order:
        chan = {}

        i_b = pos + i_ch * CHAN_LENGTH

        chan["status"] = f[i_b : i_b + 1]
        i_b += 1  # Status of electrode for acquisition : 0 : not acquired, 1 : acquired
        chan["channelType"] = f[i_b : i_b + 1]
        i_b += 1  # TODO: type of reference

        chan["chan_name"] = f[i_b : i_b + 6].strip(b"\x01\x00").decode(ENCODING)
        i_b += 6
        chan["ground"] = f[i_b : i_b + 6].strip(b"\x01\x00").decode(ENCODING)
        i_b += 6
        l_min, l_max, chan["logical_ground"], ph_min, ph_max = unpack(
            "iiiii", f[i_b : i_b + 20]
        )
        i_b += 20
        chan["factor"] = float(ph_max - ph_min) / float(l_max - l_min + 1)

        k = unpack("h", f[i_b : i_b + 2])[0]
        i_b += 2
        chan["units"] = UNITS.get(k, UNITS[0])

        chan["HiPass_Limit"], chan["HiPass_Type"] = unpack("HH", f[i_b : i_b + 4])
        i_b += 4
        chan["LowPass_Limit"], chan["LowPass_Type"] = unpack("HH", f[i_b : i_b + 4])
        i_b += 4

        chan["rate_coefficient"], chan["position"] = unpack("HH", f[i_b : i_b + 4])
        i_b += 4
        chan["Latitude"], chan["Longitude"] = unpack("ff", f[i_b : i_b + 8])
        i_b += 8
        chan["presentInMap"] = unpack("B", f[i_b : i_b + 1])[0]
        i_b += 1
        chan["isInAvg"] = unpack("B", f[i_b : i_b + 1])[0]
        i_b += 1
        chan["Description"] = f[i_b : i_b + 32].strip(b"\x01\x00").decode(ENCODING)
        i_b += 32
        chan["xyz"] = unpack("fff", f[i_b : i_b + 12])
        i_b += 12
        chan["Coordinate_Type"] = unpack("H", f[i_b : i_b + 2])[0]
        i_b += 2
        chan["free"] = f[i_b : i_b + 24].strip(b"\x01\x00")
        i_b += 24

        chans.append(chan)

    return chans


def _read_montage(f, zone):
    pos, length = zone
    i_b = pos

    montages = []

    while i_b < (pos + length):
        montage = {
            "lines": unpack("H", f[i_b : i_b + 2])[0],
            "sectors": unpack("H", f[i_b + 2 : i_b + 4])[0],
            "base_time": unpack("H", f[i_b + 4 : i_b + 6])[0],
            "notch": unpack("H", f[i_b + 6 : i_b + 8])[0],
            "colour": unpack(MAX_CAN_VIEW * "B", f[i_b + 8 : i_b + 136]),
            "selection": unpack(MAX_CAN_VIEW * "B", f[i_b + 136 : i_b + 264]),
            "description": f[i_b + 264 : i_b + 328].strip(b"\x01\x00").decode(ENCODING),
            "inputsNonInv": unpack(
                MAX_CAN_VIEW * "H", f[i_b + 328 : i_b + 584]
            ),  # NonInv : non inverting input
            "inputsInv": unpack(
                MAX_CAN_VIEW * "H", f[i_b + 584 : i_b + 840]
            ),  # Inv : inverting input
            "HiPass_Filter": unpack(MAX_CAN_VIEW * "I", f[i_b + 840 : i_b + 1352]),
            "LowPass_Filter": unpack(MAX_CAN_VIEW * "I", f[i_b + 1352 : i_b + 1864]),
            "reference": unpack(MAX_CAN_VIEW * "I", f[i_b + 1864 : i_b + 2376]),
            "free": f[i_b + 2376 : i_b + 4096].strip(b"\x01\x00"),
        }
        i_b += 4096
        montages.append(montage)

    return montages
