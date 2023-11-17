"""Micromed Header module
Contains some description of the micromed header of type 4
"""
from dataclasses import dataclass
from datetime import datetime

MICROMED_ACQ_EQUIPMENT = {
    0: "BQ124 - 24 channels headbox, Internal Interface",
    1: "MS40 - Holter recorder",
    2: "BQ132S - 32 channels headbox, Internal Interface",
    6: "BQ124 - 24 channels headbox, BQ CARD Interface",
    7: "SAM32 - 32 channels headbox, BQ CARD Interface",
    8: "SAM25 - 25 channels headbox, BQ CARD Interface",
    9: "BQ132S R - 32 channels reverse headbox, Internal Interface",
    10: "SAM32 R - 32 channels reverse headbox, BQ CARD Interface",
    11: "SAM25 R - 25 channels reverse headbox, BQ CARD Interface",
    12: "SAM32 - 32 channels headbox, Internal Interface",
    13: "SAM25 - 25 channels headbox, Internal Interface",
    14: "SAM32 R - 32 channels reverse headbox, Internal Interface",
    15: "SAM25 R - 25 channels reverse headbox, Internal Interface",
    16: "SD - 32 channels headbox with jackbox, SD CARD Interface – PCI Internal Interface",
    17: "SD128 - 128 channels headbox, SD CARD Interface – PCI Internal Interface",
    18: "SD96 - 96 channels headbox, SD CARD Interface – PCI Internal Interface",
    19: "SD64 - 64 channels headbox, SD CARD Interface – PCI Internal Interface",
    20: "SD128c - 128 channels headbox with jackbox, SD CARD Interface – PCI Internal Interface",
    21: "SD64c - 64 channels headbox with jackbox, SD CARD Interface – PCI Internal Interface",
    22: "BQ132S - 32 channels headbox, PCI Internal Interface",
    23: "BQ132S R - 32 channels reverse headbox, PCI Internal Interface",
}


@dataclass
class ElectrodeReferences:
    """Electrode references for conversion purpose

    See also
    --------
    MicromedHeader
    """

    logic_min: int = None
    logic_max: int = None
    logic_ground: int = None
    phy_min: int = None
    phy_max: int = None
    units: int = None


@dataclass
class MicromedHeader:
    """Micromed Header data

    The header is common between TRC files and TCP communication. It contains the info to decode
    the data correctly and some experiment info.

    This class extract *some* of the available info.

    Parameters
    ----------
    surname : str, optional
        The patient surname.
    name : str, optional
        The patient name.
    nb_of_channels : int, optional
        The number of channels.
    acq_unit : int, optional
        The acquisition unit
    min_sampling_rate: int, optional
        The minimum sampling rate of EEGs channels.
    nb_of_bytes: int, optional
        The number of bytes on which eeg data is encoded per value. Should be in [1, 2, 4].

        .. warning::
            When selecting a 24-bits resolution in SystemPLUS, values are encoded on 4 bytes...

    header_type: int, optional
        The header type. To be checked for valid parsing.
    stored_channels: int, optional
        Number of stored channels in EEGs data.
    ch_names: list, optional
        The channel names.
    elec_refs: List[ElectrodeReferences], optional
        A list of electrode references.
    data_address: int, optional
        The byte address of data packet start (useless in TCP context)
    note_address : int, optional
        The byte address of note packet start (useless in TCP context)

    Attributes
    ----------
    surname : str
        The patient surname.
    name : str
        The patient name.
    nb_of_channels : int
        The number of channels.
    acq_unit : int, optional
        The acquisition unit
    min_sampling_rate: int
        The minimum sampling rate of EEGs channels.
    nb_of_bytes: int
        The number of bytes on which eeg data is encoded per value. Should be in [1, 2, 4].

        .. warning::
            When selecting a 24-bits resolution in SystemPLUS, values are encoded on 4 bytes...

    header_type: int
        The header type. To be checked for valid parsing.
    stored_channels: int
        Number of stored channels in EEGs data.
    ch_names: list
        The channel names.
    elec_refs: List[ElectrodeReferences]
        A list of electrode references.
    data_address: int
        The byte address of data packet start (useless in TCP context).
    note_address : int
        The byte address of note packet start (useless in TCP context)
    recording_date: datetime
        The date of file creation and therefore the recording date.
    notes : dict
        Notes entered in Micromed interface. Keys are samples and values are comments.
    markers : dict
        Serial markers received by Micromed. Key is the sample and value is the marker value.
    """

    surname: str = None
    name: str = None
    nb_of_channels: int = None
    order: list = None
    acq_unit: int = None
    min_sampling_rate: int = None
    nb_of_bytes: int = None
    header_type: int = None
    stored_channels: int = None
    ch_names: list = None
    # elec_refs is a list of electrode references. Dim 2 is
    # [logic_min, logic_max, logic_ground, phy_min, phy_max, units]
    elec_refs: list = None
    data_address: int = None
    recording_date: datetime = None
    notes: dict = None
    markers: dict = None
