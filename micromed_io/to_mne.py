"""Micromed module to load and transform data from Micromed recordings to mne format"""
from datetime import timezone
from pathlib import Path
from typing import List, Union

import mne
import numpy as np
from micromed_io.header import MICROMED_ACQ_EQUIPMENT
from micromed_io.in_out import MicromedIO


def get_indexes(l1: list, l2: list) -> list:
    """Extract indexes of list ``l1`` items from list ``l2``

    Parameters
    ----------
    l1 : list
        The list of items to get the indexes
    l2 : list
        The list from which to extract the indexes

    Returns
    -------
    np.ndarray
        A numpy 1d-array containing the indexes in ``l2`` of items from ``l1``

    Notes
    -----
    The function works only if all items from ``l1`` are present once and only once in ``l2``
    """
    indexes = []
    for item1 in l1:
        for i, item2 in enumerate(l2):
            if item1 == item2:
                indexes.append(i)
                break
    return np.array(indexes)


def create_mne_from_micromed_recording(
    recording_file: Union[str, Path],
    sub_channels: List[str] = None,
    ch_types: Union[List[str], str] = "eeg",
) -> mne.io.RawArray:
    """Create a mne Raw instance from a Micromed recording

    Parameters
    ----------
    recording_file : Union[str, Path]
        The micromed recording file
    sub_channels : List[str], optional
        The channels to pick from the recording. If None, all channels are picked.
    ch_types: Union[List[str], str], optional
        The list of channel types. Types must be in ``['grad', 'mag', 'ref_meg', 'eeg',
        'seeg', 'dbs', 'ecog', 'eog', 'emg', 'ecg', 'resp', 'bio', 'misc', 'stim', 'exci',
        'syst', 'ias', 'gof', 'dipole', 'chpi', 'fnirs_cw_amplitude', 'fnirs_fd_ac_amplitude',
        'fnirs_fd_phase', 'fnirs_od', 'hbo', 'hbr', 'csd']``

    Returns
    -------
    mne.io.RawArray
        A mne Raw instance containing the requested channels

    Notes
    -----
    Some info are hardcoded, such as:

    - ``device_info`` type: Micromed
    - ``device_info`` site: Unknown

    Update the code if needed

    Examples
    --------
    >>> from micromed_io.to_mne import create_mne_from_micromed_recording
    >>> mne_raw = create_mne_from_micromed_recording("path/to/file.TRC")

    """
    with open(recording_file, "rb") as f:
        data = f.read()

    micromed_io = MicromedIO()
    micromed_io.decode_data_header_packet(data)
    micromed_io.decode_operator_note_packet(
        data[micromed_io.micromed_header.note_address :]
    )
    micromed_io.decode_data_eeg_packet(data[micromed_io.micromed_header.data_address :])

    if sub_channels is None:
        sub_channels = micromed_io.micromed_header.ch_names

    sub_channels_ids = get_indexes(sub_channels, micromed_io.micromed_header.ch_names)
    sub_eegs = micromed_io.current_data_eeg[sub_channels_ids, :]

    info = mne.create_info(
        ch_names=sub_channels,
        sfreq=micromed_io.micromed_header.min_sampling_rate,
        ch_types=ch_types,
    )
    info["device_info"] = {
        "type": "Micromed",
        "model": MICROMED_ACQ_EQUIPMENT[micromed_io.micromed_header.acq_unit]
        if micromed_io.micromed_header.acq_unit in MICROMED_ACQ_EQUIPMENT
        else str(micromed_io.micromed_header.acq_unit),
        "site": "Unknown",
    }
    info["subject_info"] = {
        "his_id": micromed_io.micromed_header.name,
        "sex": 0,
    }

    raw = mne.io.RawArray(
        sub_eegs,
        info,
    )
    raw.set_meas_date(
        micromed_io.micromed_header.recording_date.replace(tzinfo=timezone.utc)
    )

    # Add annotations from recording
    for sample_note, comment in micromed_io.notes.items():
        raw.annotations.append(
            onset=sample_note / info["sfreq"], duration=0, description=comment
        )

    return raw
