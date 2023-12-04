# Micromed library

Library to handle Micromed data. Main features:

* simulate online data from a trc file
* push online tcp data to LSL server
* convert trc to mne format
* rename trc files to include the recording datetime

## Install

``` bash
pip install micromed-io
```

## Convert a Micromed (*.trc*) file to MNE (*.fif*) format

``` python
from micromed_io.to_mne import create_mne_from_micromed_recording
mne_raw = create_mne_from_micromed_recording("path/to/file.TRC")
```

## Emulate Online Micromed TCP from *.trc* file

``` bash
mmio_emulate_trc --file=../data/sample.TRC --address=localhost --port=5123
```

Emulate the online data stream of Micromed to test your real-time platform.
See all the arguments and adapt them:

``` bash
mmio_emulate_trc --help # to see all arguments
```

> **New**: not only data, but also markers and notes are send through TCP, exactly as Micromed does

## Read TCP and push to LSL Stream

``` bash
mmio_tcp_to_lsl --address=localhost --port=5123
```

While receiving online data throug tcp, this command forward the data to 3 LSL stream outlets:

* Micromed_EEG: the eeg data in ``float32`` format ``[n_channels, n_samples]``
* Micromed_Markers: markers if any in ``int32`` format ``[sample, marker]`` (2 channels)
* Micromed_Notes: notes if any in ``string`` format ``[sample, note]`` (2 channels)

You can easily change the LSL parameters:

``` bash
mmio_tcp_to_lsl --help # to see all arguments
```

## Read TRC file

``` python
from micromed_io.trc import MicromedTRC
mmtrc = MicromedTRC("sample.TRC")
```
Then you have access to the *trc* data:
``` python
mmtrc.get_header()
mmtrc.get_markers()
mmtrc.get_data()
mmtrc.get_notes()
```
> **Note:** ``get_data()`` might take times because it loads the brain data

## Read and parse Micromed TCP live data

Download `tcp_to_lsl.py` from the [gihub repo](https://github.com/etiennedemontalivet/micromed-io) in *scripts/*
``` bash
python tcp_to_lsl.py --address=localhost --port=5123
```

> **Note**: Micromed TCP behaves as a client. If you want to try the emulate/read TCP script, launch the reader first that acts as server, then the emulator. 

## Read Micromed TCP in a sliding window buffer

If you plan to use the Micromed data as input of a decoder, you probably want epochs of format `(n_channels, n_samples)`. Then the ``MicromedBuffer`` class is for you. The script ``read_tcp_to_epoch.py`` show you how to use it (see the ``PROCESS HERE`` comment). It uses a **buffer** that mimics the **sliding window** and triggers each time it is filled.

``` python
from micromed_io.buffer import MicromedBuffer
micromed_buffer = MicromedBuffer(epoch_duration=5, epoch_overlap=2.5)
```

## Rename TRC files with recording datetime

``` bash
mmio_rename_trc --dirpath=./ --format=%Y%m%d-%H%M%S
```

Rename the TRC files of the given folder to include the recording date in the filename.
Output is : ``<filename>__<recording_date>.TRC``.
The format must be compliant with python [strftime format codes](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes)

``` bash
mmio_rename_trc --help # to see help
```


## Local install

Download the repo and:

```
conda env create -f environment.yml
conda activate mmio
poetry install
```


## TODO

- [x] Include serial markers parsing
- [ ] Parse all info from Micromed header
- [x] Emulate serial markers + notes

Please feel free to reach me if you want to contribute.
