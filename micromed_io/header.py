"""Micromed Header module
Contains some description of the micromed header of type 4
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ElectrodeReferences:
    """Electrode references for conversion purpose

    See also
    --------
    MicromedHeader
    """

    factor: float = None  # float(ph_max - ph_min) / float(l_max - l_min + 1)
    logic_ground: int = None
    units: str = None


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
        Notes entered in Micromed interface. Keys are samples and values are comments (str).
    markers : dict
        Serial markers received by Micromed. Key is the sample and value is the marker value (str).
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
    # [factor, logic_ground, units]
    elec_refs: list = None
    data_address: int = None
    recording_date: datetime = None
    notes: dict = None
    markers: dict = None
