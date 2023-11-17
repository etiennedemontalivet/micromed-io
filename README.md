# Micromed library

Library to handle Micromed data. It also provides some useful scripts.

## Install

``` bash
pip install micromed-io
```

## Convert a Micromed (*.trc*) file to MNE (*.fif*) format

``` python
from micromed_io.to_mne import create_mne_from_micromed_recording
mne_raw = create_mne_from_micromed_recording("path/to/file.TRC")
```

## Emulate Micromed TCP from *.trc* file

### CLI tool

Use the following command:

``` bash
mmio_tcp_emulator --file=../data/sample.TRC --address=localhost --port=5123
mmio_tcp_emulator --help
```

### From python script

Download `emulate_trc_tcpip.py` from the [gihub repo](https://github.com/etiennedemontalivet/micromed-io) in *scripts/*

``` bash
python emulate_trc_tcpip.py --file=../data/sample.TRC --address=localhost --port=5123
```

More details:
``` bash
python emulate_trc_tcpip.py --help
```

## Read and parse Micromed TCP live data

Download `read_tcp_data.py` from the [gihub repo](https://github.com/etiennedemontalivet/micromed-io) in *scripts/*
``` bash
python read_tcp_data.py --address=localhost --port=5123
```

> **Note**: Micromed TCP behaves as a client. If you want to try the emulate/read TCP script, launch the reader first that acts as server, then the emulator. 

## Read Micromed TCP in a sliding window buffer

If you plan to use the Micromed data as input of a decoder, you probably want epochs of format `(n_channels, n_samples)`. Then the ``MicromedBuffer`` class is for you. The script ``read_tcp_to_epoch.py`` show you how to use it (see the ``PROCESS HERE`` comment). It uses a **buffer** that mimics the **sliding window** and triggers each time it is filled.

``` python
from micromed_io.buffer import MicromedBuffer
micromed_buffer = MicromedBuffer(epoch_duration=5, epoch_overlap=2.5)

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

## TODO

- [x] Include serial markers parsing
- [ ] Parse all info from Micromed header
- [ ] Emulate serial markers + notes

Please feel free to reach me if you want to contribute.
