"""Micromed module to load and transform data from Micromed recordings to mne format"""
from datetime import timezone
from pathlib import Path
from typing import List, Union

import mne
import numpy as np
from micromed_io.trc import MicromedTRC


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
    micromed_trc = MicromedTRC(recording_file)

    if sub_channels is None:
        sub_channels = micromed_trc.micromed_header.ch_names
    sub_eegs = micromed_trc.get_data(picks=sub_channels)

    info = mne.create_info(
        ch_names=sub_channels,
        sfreq=micromed_trc.sfreq,
        ch_types=ch_types,
    )
    info["device_info"] = {
        "type": "Micromed",
        "model": micromed_trc.micromed_header.acq_unit,
        "site": micromed_trc._header["laboratory"],
    }
    info["subject_info"] = {
        "his_id": micromed_trc.micromed_header.name,
        "sex": 0,
    }

    raw = mne.io.RawArray(
        sub_eegs,
        info,
    )
    raw.set_meas_date(
        micromed_trc.micromed_header.recording_date.replace(tzinfo=timezone.utc)
    )

    # Add annotations from notes
    for note_sample, note_val in micromed_trc.get_notes().items():
        raw.annotations.append(
            onset=note_sample / info["sfreq"], duration=0, description=note_val
        )

    # Add annotations from markers
    for marker_sample, marker_val in micromed_trc.get_markers().items():
        raw.annotations.append(
            onset=marker_sample / info["sfreq"], duration=0, description=marker_val
        )

    return raw
