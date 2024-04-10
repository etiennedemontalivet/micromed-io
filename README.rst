Micromed IO library
===================

|Tests|_ |Doc|_ |Codecov|_

.. |Tests| image:: https://github.com/etiennedemontalivet/micromed-io/actions/workflows/tests.yml/badge.svg
.. _Tests: https://github.com/etiennedemontalivet/micromed-io/actions/workflows/tests.yml

.. |Doc| image:: https://github.com/etiennedemontalivet/micromed-io/actions/workflows/documentation.yml/badge.svg
.. _Doc: https://github.com/etiennedemontalivet/micromed-io/actions/workflows/documentation.yml

.. |Codecov| image:: https://codecov.io/gh/etiennedemontalivet/micromed-io/graph/badge.svg?token=X6UBEUW767
.. _Codecov: https://codecov.io/gh/etiennedemontalivet/micromed-io

A library to read, emulate, and forward Micromed data in standard formats. See 
`online doc <https://etiennedemontalivet.github.io/micromed-io/>`__.

Main features:

-  simulate online data from a trc file
-  push online tcp data to LSL server
-  convert trc to mne format
-  rename trc files to include the recording datetime

Install
-------

.. code:: bash

   $ pip install micromed-io


Convert a Micromed (*.trc*) file to MNE (*.fif*) format
-------------------------------------------------------

.. code:: python

   from micromed_io.to_mne import create_mne_from_micromed_recording
   mne_raw = create_mne_from_micromed_recording("path/to/file.TRC")


Emulate TRC to TCP & read/forward to LSL server
------------------------------------------------
See details in next sections

.. image:: https://raw.githubusercontent.com/etiennedemontalivet/micromed-io/master/docs/source/data/mmio_server.gif
   :alt: StreamPlayer
   :align: center


.. _emulate TRC:

Emulate Online Micromed TCP from *.trc* file
--------------------------------------------

.. code:: bash

   $ mmio_emulate_trc --file=../data/sample.TRC --address=localhost --port=5123


Emulate the online data stream of Micromed to test your real-time
platform. See all the arguments and adapt them:


.. code:: bash

   $ mmio_emulate_trc --help # to see all arguments

.. note::

   **New**: not only data, but also markers and notes are send through
   TCP, exactly as Micromed does


Read TCP and push to LSL Stream
-------------------------------

.. code:: bash

   $ mmio_tcp_to_lsl --address=localhost --port=5123

While receiving online data throug tcp, this command forward the data to
3 LSL stream outlets:

-  Micromed_EEG: the eeg data in ``float32`` format
   ``[n_channels, n_samples]``
-  Micromed_Markers: markers if any in ``int32`` format
   ``[sample, marker]`` (2 channels)
-  Micromed_Notes: notes if any in ``string`` format ``[sample, note]``
   (2 channels)

You can easily change the LSL parameters:

.. code:: bash

   $ mmio_tcp_to_lsl --help # to see all arguments


Read TRC file
-------------

.. code:: python

   from micromed_io.trc import MicromedTRC
   mmtrc = MicromedTRC("sample.TRC")

Then you have access to the *trc* data:

.. code:: python

   mmtrc.get_header()
   mmtrc.get_markers()
   mmtrc.get_data()
   mmtrc.get_notes()

.. note::

   **Note:** ``get_data()`` might take times because it loads the brain
   data

Read and parse Micromed TCP live data
-------------------------------------

Download ``tcp_to_lsl.py`` from the `github
repo <https://github.com/etiennedemontalivet/micromed-io>`__ in
*scripts/*

.. code:: bash

   $ python tcp_to_lsl.py --address=localhost --port=5123

..

   **Note**: Micromed TCP behaves as a client. If you want to try the
   emulate/read TCP script, launch the reader first that acts as server,
   then the emulator.


Rename TRC files with recording datetime
----------------------------------------

.. code:: bash

   $ mmio_rename_trc --dirpath=./ --format=%Y%m%d-%H%M%S

Rename the TRC files of the given folder to include the recording date
in the filename. Output is : ``<filename>__<recording_date>.TRC``. The
format must be compliant with python `strftime format
codes <https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes>`__

.. code:: bash

   mmio_rename_trc --help # to see help

Local install
-------------

Download the repo and:

.. code:: bash

   $ conda env create -f environment.yml
   $ conda activate mmio
   $ poetry install


Please feel free to reach me if you want to contribute.

Sponsor
-------

This work has been supported by the Wyss Center.

.. image:: https://raw.githubusercontent.com/etiennedemontalivet/micromed-io/master/docs/source/data/wyss-center-full.png
  :alt: Wyss Center logo
  :align: center
  :class: only-light
  :width: 50%

.. image:: https://raw.githubusercontent.com/etiennedemontalivet/micromed-io/master/docs/source/data/wyss-center-full-inverse.png
  :alt: Wyss Center inverse logo
  :align: center
  :class: only-dark
  :width: 50%