from pathlib import Path

import yaml

from cascadeguard_graph.builder import GraphBuilder
from cascadeguard_graph.rebuild import diff_timetable, rebuild_if_changed
from cascadeguard_graph.store import GraphStore
from cascadeguard_sim.network import SectionNetwork
from cascadeguard_sim.timetable import Timetable

CONFIG = str(
    Path(__file__).resolve().parents[2] / "simulator" / "config" / "section.example.yaml"
)


def _graph():
    return GraphBuilder(SectionNetwork.from_yaml(CONFIG), Timetable.from_yaml(CONFIG)).build()


def _etypes(g):
    return {d["etype"] for _, _, d in g.edges(data=True)}


def test_graphml_round_trips(tmp_path):
    g = _graph()
    store = GraphStore()
    path = tmp_path / "section.graphml"
    store.export(g, str(path), fmt="graphml")

    loaded = store.load(str(path))
    assert loaded.number_of_nodes() == g.number_of_nodes()
    assert loaded.number_of_edges() == g.number_of_edges()
    assert {d["ntype"] for _, d in loaded.nodes(data=True)} == {"station", "service"}
    assert _etypes(loaded) == _etypes(g)


def test_geojson_export_is_a_feature_collection(tmp_path):
    g = _graph()
    path = tmp_path / "section.geojson"
    GraphStore().export(g, str(path), fmt="geojson")
    doc = __import__("json").loads(path.read_text())
    assert doc["type"] == "FeatureCollection"
    assert len(doc["features"]) == g.number_of_nodes()


def _modified_config(tmp_path, mutate) -> str:
    cfg = yaml.safe_load(Path(CONFIG).read_text())
    mutate(cfg)
    out = tmp_path / "modified.yaml"
    out.write_text(yaml.safe_dump(cfg))
    return str(out)


def test_no_change_does_not_rebuild():
    store = GraphStore()
    assert rebuild_if_changed(store, CONFIG, CONFIG) is False
    assert store.graph is None


def test_added_service_triggers_rebuild(tmp_path):
    def add_service(cfg):
        cfg["services"].append(
            {"train_no": "99999", "stops": [{"station": "PNBE", "dep": 5},
                                            {"station": "MGS", "arr": 45, "dep": 50},
                                            {"station": "BSB", "arr": 60}]}
        )

    new_path = _modified_config(tmp_path, add_service)
    diff = diff_timetable(CONFIG, new_path)
    assert diff["added"] == ["99999"] and not diff["removed"] and not diff["changed"]

    store = GraphStore()
    assert rebuild_if_changed(store, CONFIG, new_path) is True
    assert "service:99999" in store.graph


def test_changed_schedule_triggers_rebuild(tmp_path):
    def shift_time(cfg):
        cfg["services"][0]["stops"][1]["arr"] = 999  # move 12301's MGS arrival

    new_path = _modified_config(tmp_path, shift_time)
    assert diff_timetable(CONFIG, new_path)["changed"] == ["12301"]
    assert rebuild_if_changed(GraphStore(), CONFIG, new_path) is True
