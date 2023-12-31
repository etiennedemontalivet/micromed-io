import datetime
import os
from pathlib import Path

import mne
import pytest

from micromed_io.to_mne import create_mne_from_micromed_recording


def test_create_mne_from_micromed_recording():
    # Define the path to the sample TRC file
    trc_file = Path(os.path.dirname(__file__)) / ".." / "data" / "sample.TRC"

    # Call the function with the sample TRC file
    raw = create_mne_from_micromed_recording(trc_file)

    # Assert the expected results
    assert isinstance(raw, mne.io.RawArray)
    assert raw.info["sfreq"] == 2048
    assert raw.info["ch_names"] == [
        "x1-G2",
        "x2-G2",
        "x3-G2",
        "x4-G2",
        "x5-G2",
        "x6-G2",
        "x7-G2",
        "x8-G2",
        "x9-G2",
        "x10-G2",
        "MKR1+-MKR1-",
        "MKR2+-MKR2-",
        "MKR3+-MKR3-",
        "MKR4+-MKR4-",
    ]
    assert raw.info["meas_date"] == datetime.datetime(
        2023, 11, 6, 14, 35, 6, tzinfo=datetime.timezone.utc
    )
    assert raw.info["device_info"]["type"] == "Micromed"
    assert raw.info["device_info"]["model"] == "65"
    assert raw.info["device_info"]["site"] == ""
    assert raw.info["subject_info"]["his_id"] == "Chb"
    assert raw.annotations.onset.tolist() == [
        0.03125,
        6.90625,
        28.26220703125,
        28.51611328125,
        28.76904296875,
        29.02099609375,
        29.27294921875,
        29.52490234375,
        29.77978515625,
        32.97705078125,
        33.48486328125,
        33.99072265625,
        35.49560546875,
        36.0,
        36.5,
        37.0,
        38.5,
        39.0,
        39.5,
        40.0,
        41.50341796875,
        42.00927734375,
        42.51416015625,
        43.01904296875,
        44.52294921875,
        45.02783203125,
        45.53125,
        46.03125,
        47.53125,
        48.03125,
        48.53125,
        49.03125,
        50.54541015625,
        50.79833984375,
        51.05322265625,
        54.51318359375,
        55.01806640625,
        55.52294921875,
        57.02783203125,
        57.53125,
        58.03125,
        58.53125,
        60.03125,
        60.53125,
        61.03125,
        61.53173828125,
        63.03662109375,
        63.54150390625,
        64.04541015625,
        64.55126953125,
        66.05712890625,
        66.56103515625,
        67.0625,
        67.5625,
        69.0625,
        69.5625,
        70.0625,
        70.5625,
        72.06298828125,
        72.31396484375,
        72.58740234375,
        75.49462890625,
        75.99853515625,
        76.5,
        78.0,
        78.5,
        79.0,
        79.5,
        81.00341796875,
        81.50927734375,
        82.01318359375,
        82.51806640625,
        84.02294921875,
        84.52783203125,
        85.03125,
        85.53125,
        87.03125,
        87.53125,
        88.03125,
        88.53125,
        90.03173828125,
        90.53662109375,
        91.04248046875,
        91.54541015625,
        93.04931640625,
        93.30126953125,
        93.55615234375,
        96.10791015625,
        96.61181640625,
        97.11669921875,
        98.62158203125,
        99.125,
        99.625,
        100.125,
        101.625,
        102.125,
        102.625,
        103.12548828125,
        104.62939453125,
        105.13525390625,
        105.63916015625,
        106.14404296875,
        107.64892578125,
        108.15380859375,
        108.65625,
        109.15625,
        110.65625,
        111.15625,
        111.65625,
        112.15625,
        113.65673828125,
        113.90771484375,
        114.16162109375,
        117.21875,
        117.72119140625,
        118.22607421875,
        119.73095703125,
        120.23583984375,
        120.74072265625,
        121.24560546875,
        122.74951171875,
        123.25,
        123.75,
        124.25,
        125.75,
        126.25,
        126.75,
        127.25244140625,
        128.75732421875,
        129.26318359375,
        129.76806640625,
        130.27294921875,
        131.77783203125,
        132.28125,
        132.78125,
        133.28125,
        134.78125,
        135.03125,
        135.28125,
        138.57275390625,
        139.07666015625,
        139.58251953125,
        141.08740234375,
        141.59130859375,
        142.09375,
        142.59375,
        144.09375,
        144.59375,
        145.09375,
        145.59814453125,
        146.33447265625,
        152.8125,
        153.59375,
        154.09375,
        154.59375,
        155.09375,
        156.59375,
        157.09619140625,
        157.60107421875,
        158.12353515625,
        159.625,
        160.125,
        160.625,
        161.125,
        162.625,
    ]
    assert raw.annotations.description.tolist() == [
        "TCP connection failed",
        "17",
        "17",
        "20",
        "32",
        "40",
        "14",
        "101",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "14",
        "102",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "14",
        "101",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "14",
        "102",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "14",
        "101",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "14",
        "102",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "16",
        "17",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "3",
        "2",
        "1",
        "4",
        "11",
    ]

    # Call the function with the sample TRC file
    raw = create_mne_from_micromed_recording(trc_file, start_time=20, stop_time=30)

    # Assert the expected results
    assert isinstance(raw, mne.io.RawArray)
    assert raw.info["sfreq"] == 2048
    assert raw.info["ch_names"] == [
        "x1-G2",
        "x2-G2",
        "x3-G2",
        "x4-G2",
        "x5-G2",
        "x6-G2",
        "x7-G2",
        "x8-G2",
        "x9-G2",
        "x10-G2",
        "MKR1+-MKR1-",
        "MKR2+-MKR2-",
        "MKR3+-MKR3-",
        "MKR4+-MKR4-",
    ]
    assert raw.info["meas_date"] == datetime.datetime(
        2023, 11, 6, 14, 35, 26, tzinfo=datetime.timezone.utc
    )
    assert raw.info["device_info"]["type"] == "Micromed"
    assert raw.info["device_info"]["model"] == "65"
    assert raw.info["device_info"]["site"] == ""
    assert raw.info["subject_info"]["his_id"] == "Chb"
    assert raw.annotations.onset.tolist() == [
        8.26220703125,
        8.51611328125,
        8.76904296875,
        9.02099609375,
        9.27294921875,
        9.52490234375,
        9.77978515625,
    ]
    assert raw.annotations.description.tolist() == [
        "17",
        "20",
        "32",
        "40",
        "14",
        "101",
        "3",
    ]
