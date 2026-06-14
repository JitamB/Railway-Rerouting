from pathlib import Path

from cascadeguard_sim.timetable import Timetable

CONFIG = Path(__file__).resolve().parents[1] / "config" / "section.example.yaml"


def test_from_yaml_parses_services_and_rake_links():
    tt = Timetable.from_yaml(str(CONFIG))

    trains = [s.train_no for s in tt.services()]
    assert trains == ["12301", "12302", "12303", "15049"]

    svc = tt.service("12301")
    assert svc.stops == ["PNBE", "MGS", "BSB"]
    assert "PNBE" not in svc.sched_arr_min  # origin has no arrival
    assert svc.sched_dep_min["PNBE"] == 0
    assert svc.sched_arr_min["BSB"] == 55

    links = tt.rake_links()
    assert len(links) >= 1
    assert (links[0].inbound, links[0].outbound) == ("12301", "12302")
    assert links[0].min_turnaround_min == 15
