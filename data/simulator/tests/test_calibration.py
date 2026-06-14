from pathlib import Path

from cascadeguard_sim.calibration import calibrate
from cascadeguard_sim.network import SectionNetwork
from cascadeguard_sim.timetable import Timetable

CONFIG = str(Path(__file__).resolve().parents[1] / "config" / "section.example.yaml")


def _net_tt():
    return SectionNetwork.from_yaml(CONFIG), Timetable.from_yaml(CONFIG)


def test_no_dump_returns_documented_defaults():
    net, tt = _net_tt()
    out = calibrate(net, tt, "does/not/exist.csv")
    assert out["calibrated"] is False
    assert out["running_time_factor"] == 1.0
    assert out["station_delay_bias_min"] == {}


def test_fits_per_station_bias_from_csv(tmp_path):
    dump = tmp_path / "hist.csv"
    dump.write_text(
        "train_no,station,delay_min\n"
        "12301,MGS,10\n"
        "12303,MGS,20\n"
        "12301,BSB,4\n"
        "99999,ZZZ,99\n"  # station outside the section -> ignored
    )
    net, tt = _net_tt()
    out = calibrate(net, tt, str(dump))

    assert out["calibrated"] is True
    assert out["n_records"] == 3  # ZZZ dropped
    assert out["station_delay_bias_min"]["MGS"] == 15.0  # mean(10, 20)
    assert out["station_delay_bias_min"]["BSB"] == 4.0
    assert "ZZZ" not in out["station_delay_bias_min"]
