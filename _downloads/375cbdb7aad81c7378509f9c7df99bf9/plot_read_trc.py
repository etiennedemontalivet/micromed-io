"""
===================
Read TRC file data
===================

Here we read a trc file recorded with a Micromed system. We access the header, the notes, 
the markers and the data.
"""
# Author: Etienne de Montalivet <etienne.demontalivet@protonmail.com>
#
# License: BSD-3-Clause

# %%
from micromed_io.trc import MicromedTRC
from pathlib import Path

fname = Path("../data/sample.TRC")
mmtrc = MicromedTRC(fname)
# %%
# To get most useful data from the header, you can use ``micromed_header``
print(mmtrc.micromed_header)
hdr = mmtrc.micromed_header
print(
    f"Participant {hdr.name}-{hdr.surname} recorded with {hdr.nb_of_channels} channels "
    + f"({hdr.ch_names}) at {mmtrc.sfreq}Hz with {hdr.acq_unit}."
)

# %%
# If this is not enough for you, you can look for what you need in the full ``_header``
mmtrc._header
# %%
# To extract notes from recording in the format ``{sample0 : note0, ... sampleN: noteN}``
mmtrc.get_notes()

# %%
# To extract markers from recording in the format ``{sample0 : marker0, ... sampleN: markerN}``
mmtrc.get_markers()

# %%
# If you need markers or notes times in seconds, just divide by the sampling frequency
{k / mmtrc.sfreq: v for k, v in mmtrc.get_markers().items()}

# %%
# To get and play with the data, simply use:
data = mmtrc.get_data()
print(f"data shape: {data.shape}")
# or, if you want the 1st channel data only:
data_ch1 = mmtrc.get_data(picks=[hdr.ch_names[0]])
print(f"data_ch1 shape: {data_ch1.shape}")
