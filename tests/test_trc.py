import datetime
import os
from pathlib import Path
import numpy as np

from micromed_io.trc import MicromedTRC


def test_micromed_trc():
    # Define the path to the sample TRC file
    trc_file = Path(os.path.dirname(__file__)) / ".." / "data" / "sample.TRC"

    # Create an instance of the MicromedTRC class
    micromed_trc = MicromedTRC(trc_file)

    # Test the get_header() method
    header = micromed_trc.get_header()
    assert header is not None
    assert header.nb_of_channels == 14
    assert header.ch_names == [
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
    assert header.acq_unit == "65"
    assert header.recording_date == datetime.datetime(2023, 11, 6, 14, 35, 6)

    # Test the get_sfreq() method
    sfreq = micromed_trc.get_sfreq()
    assert sfreq == 2048

    # Test the get_notes() method
    notes = micromed_trc.get_notes()
    assert notes == {64: "TCP connection failed"}

    # Test the get_markers() method
    markers = micromed_trc.get_markers()
    assert markers == {
        14144: "17",
        57881: "17",
        58401: "20",
        58919: "32",
        59435: "40",
        59951: "14",
        60467: "101",
        60989: "3",
        67537: "2",
        68577: "1",
        69613: "4",
        72695: "3",
        73728: "2",
        74752: "1",
        75776: "4",
        78848: "3",
        79872: "2",
        80896: "1",
        81920: "4",
        84999: "3",
        86035: "2",
        87069: "1",
        88103: "4",
        91183: "3",
        92217: "2",
        93248: "1",
        94272: "4",
        97344: "3",
        98368: "2",
        99392: "1",
        100416: "4",
        103517: "14",
        104035: "102",
        104557: "3",
        111643: "2",
        112677: "1",
        113711: "4",
        116793: "3",
        117824: "2",
        118848: "1",
        119872: "4",
        122944: "3",
        123968: "2",
        124992: "1",
        126017: "4",
        129099: "3",
        130133: "2",
        131165: "1",
        132201: "4",
        135285: "3",
        136317: "2",
        137344: "1",
        138368: "4",
        141440: "3",
        142464: "2",
        143488: "1",
        144512: "4",
        147585: "14",
        148099: "101",
        148659: "3",
        154613: "2",
        155645: "1",
        156672: "4",
        159744: "3",
        160768: "2",
        161792: "1",
        162816: "4",
        165895: "3",
        166931: "2",
        167963: "1",
        168997: "4",
        172079: "3",
        173113: "2",
        174144: "1",
        175168: "4",
        178240: "3",
        179264: "2",
        180288: "1",
        181312: "4",
        184385: "3",
        185419: "2",
        186455: "1",
        187485: "4",
        190565: "14",
        191081: "102",
        191603: "3",
        196829: "2",
        197861: "1",
        198895: "4",
        201977: "3",
        203008: "2",
        204032: "1",
        205056: "4",
        208128: "3",
        209152: "2",
        210176: "1",
        211201: "4",
        214281: "3",
        215317: "2",
        216349: "1",
        217383: "4",
        220465: "3",
        221499: "2",
        222528: "1",
        223552: "4",
        226624: "3",
        227648: "2",
        228672: "1",
        229696: "4",
        232769: "14",
        233283: "101",
        233803: "3",
        240064: "2",
        241093: "1",
        242127: "4",
        245209: "3",
        246243: "2",
        247277: "1",
        248311: "4",
        251391: "3",
        252416: "2",
        253440: "1",
        254464: "4",
        257536: "3",
        258560: "2",
        259584: "1",
        260613: "4",
        263695: "3",
        264731: "2",
        265765: "1",
        266799: "4",
        269881: "3",
        270912: "2",
        271936: "1",
        272960: "4",
        276032: "14",
        276544: "102",
        277056: "3",
        283797: "2",
        284829: "1",
        285865: "4",
        288947: "3",
        289979: "2",
        291008: "1",
        292032: "4",
        295104: "3",
        296128: "2",
        297152: "1",
        298185: "4",
        299693: "16",
        312960: "17",
        314560: "3",
        315584: "2",
        316608: "1",
        317632: "4",
        320704: "3",
        321733: "2",
        322767: "1",
        323837: "4",
        326912: "3",
        327936: "2",
        328960: "1",
        329984: "4",
        333056: "11",
    }

    # Test the get_data() method
    data = micromed_trc.get_data()
    assert data.shape == (14, 349632)
    data = micromed_trc.get_data(start=0, stop=10)
    assert data.shape == (14, 10)
    data = micromed_trc.get_data(start=2048, stop=4096)
    assert data.shape == (14, 2048)
    data = micromed_trc.get_data(picks=["x1-G2", "x2-G2"])
    assert data.shape == (2, 349632)

    # test the units
    ch0 = micromed_trc.micromed_header.ch_names[0]
    unit0 = micromed_trc.micromed_header.elec_refs[0].units  # string
    if unit0 == "nV":
        unit0 = 1e-9
    elif unit0 == "μV":
        unit0 = 1e-6
    elif unit0 == "mV":
        unit0 = 1e-3
    elif unit0 == "V":
        unit0 = 1
    assert np.isclose(
        micromed_trc.get_data(picks=[ch0], stop=1000, use_volt=True),
        micromed_trc.get_data(picks=[ch0], stop=1000) * unit0,
    ).all()
