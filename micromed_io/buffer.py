"""Micromed IO module
"""

from typing import List
import logging
import numpy as np

from micromed_io.in_out import MicromedIO


class MicromedBuffer(MicromedIO):
    # pylint: disable=line-too-long
    """Micromed IO class

    This class TODO

    Parameters
    ----------
    epoch_duration: float, default=None
        The epoch duration in sec.
    epoch_overlap: float, default=None
        The epoch overlap in sec.

    Attributes
    ----------
    epoch_duration: float
        The epoch duration in sec.
    epoch_overlap: float
        The epoch overlap in sec.
    epoch_buffer: np.ndarray
        The epoch buffer that is filled every new eeg packet received. (see Notes 2.)
    current_buffer_length: int
        The position of the next eeg data to fill. (see Notes 1.)
    current_epoch: np.ndarray
        The last full epoch.

    Notes
    -----
    #. The epoch buffer works this way:

        - each time we receive new data, we fill the buffer with the selected channels (cf ``picks``)
        - we keep the position of the "filled data" in current_buffer_length
        - as soon as an epoch_buffer is full, the array is stored in current_epoch and the new data \
    are filled back from current_buffer_length=0.

    #. Be careful with ``picks`` order as it changes the epoch structure (order from ``picks`` is kept). \
    ``["Fp1-G2", "Fpz-G2", "MKR+-MKR-"]`` doest not give the same epoch buffer as \
    ``["MKR+-MKR-", "Fp1-G2", "Fpz-G2"]``.


    See also
    --------
    micromed_io.header.MicromedHeader

    """

    def __init__(
        self,
        epoch_duration: float = None,
        epoch_overlap: float = None,
        picks: List[str] = None,
    ):
        MicromedIO.__init__(self, picks)
        self.epoch_duration = epoch_duration
        self.epoch_overlap = epoch_overlap
        self.epoch_buffer = None
        self.current_epoch = None
        self.current_buffer_length = 0  # count number of added eegs in buffer

    def init_buffer(self) -> None:
        """Init the epoch buffer

        Raises
        ------
        ValueError
            If `epoch_overlap` is more than 0 as it is not supported yet. Feel free to update the code.
        """
        # Construct the epoch buffer
        nb_of_samples = int(
            self.micromed_header.min_sampling_rate * self.epoch_duration
        )
        logging.debug(
            f"Creating an epoch buffer of shape [{len(self.picks_id)}, {nb_of_samples}]"
            + f". picks_id={self.picks_id}"
        )

        self.epoch_buffer = np.empty((len(self.picks_id), nb_of_samples))
        self.current_epoch = np.empty((len(self.picks_id), nb_of_samples))

    def update_epoch_buffer(self) -> bool:
        """Update of the epoch buffer

        The epoch buffer works this way:

            #. each time we receive new data, we fill the buffer
            #. we keep the position of the "filled data" in ``current_buffer_length``
            #. as soon as an ``epoch_buffer`` is full, the array is stored in ``current_epoch`` and\
            the new data are filled back from ``current_buffer_length=0``.

        Returns
        -------
        bool
            If ``True``, a new epoch has been filled and stored in ``self.current_epoch``.

        Raises
        ------
        ValueError
            If the *buffer* is not initialized before this function is called.
        """
        if self.epoch_buffer is None:
            self.init_buffer()

        has_new_epoch = False
        size_to_add = self.current_data_eeg.shape[1]
        n_overlaping_samples = int(
            self.micromed_header.min_sampling_rate * self.epoch_overlap
        )

        # if we have less new data than epoch buffer need to be filled
        if self.current_buffer_length + size_to_add < self.epoch_buffer.shape[1]:
            self.epoch_buffer[
                :, self.current_buffer_length : self.current_buffer_length + size_to_add
            ] = self.current_data_eeg[self.picks_id, :]
            self.current_buffer_length += size_to_add

        # if we have the exact number of new data needed to fill the epoch buffer
        elif self.current_buffer_length + size_to_add == self.epoch_buffer.shape[1]:
            self.epoch_buffer[
                :, self.current_buffer_length : self.current_buffer_length + size_to_add
            ] = self.current_data_eeg[self.picks_id, :]
            self.current_epoch = np.copy(self.epoch_buffer)
            self.current_buffer_length = n_overlaping_samples
            # copy the last samples to the buffer's begining (overlaping window)
            self.epoch_buffer[:, :n_overlaping_samples] = np.copy(
                self.epoch_buffer[
                    :, (self.epoch_buffer.shape[1] - n_overlaping_samples) :
                ]
            )
            has_new_epoch = True

        # if we got data overlapping the epoch buffer...
        else:
            # compute the remaining size (in buffer) and
            # over size (number of new data samples exceeding buffer)
            remaining_size = self.epoch_buffer.shape[1] - self.current_buffer_length
            over_size = size_to_add - remaining_size

            # fill the epoch buffer to construct one epoch and store it
            self.epoch_buffer[:, self.current_buffer_length :] = self.current_data_eeg[
                self.picks_id, :remaining_size
            ]
            self.current_epoch = np.copy(self.epoch_buffer)
            has_new_epoch = True

            # copy the last samples to the buffer's begining (overlaping window)
            self.epoch_buffer[:, :n_overlaping_samples] = np.copy(
                self.epoch_buffer[
                    :, (self.epoch_buffer.shape[1] - n_overlaping_samples) :
                ]
            )
            # fill the epoch buffer with the remaining samples from the new data
            self.epoch_buffer[
                :, n_overlaping_samples : (n_overlaping_samples + over_size)
            ] = np.copy(self.current_data_eeg[self.picks_id, remaining_size:])
            self.current_buffer_length = over_size + n_overlaping_samples

        return has_new_epoch
