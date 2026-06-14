from pathlib import Path

from cascadeguard_sim.network import SectionNetwork

CONFIG = Path(__file__).resolve().parents[1] / "config" / "section.example.yaml"


def test_from_yaml_loads_stations_and_blocks():
    net = SectionNetwork.from_yaml(str(CONFIG))

    codes = [s.code for s in net.stations()]
    assert codes == ["PNBE", "MGS", "BSB"]
    assert net.station("PNBE").platforms == 10

    blocks = net.block_sections()
    assert len(blocks) == 2
    assert (blocks[0].from_station, blocks[0].to_station) == ("PNBE", "MGS")
    assert blocks[0].headway_min == 5
