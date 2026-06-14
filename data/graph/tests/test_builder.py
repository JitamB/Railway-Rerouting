from pathlib import Path

from cascadeguard_graph.builder import GraphBuilder
from cascadeguard_graph.schema import SERVES, EdgeType
from cascadeguard_sim.network import SectionNetwork
from cascadeguard_sim.timetable import Timetable

CONFIG = str(
    Path(__file__).resolve().parents[2] / "simulator" / "config" / "section.example.yaml"
)


def _builder() -> GraphBuilder:
    return GraphBuilder(SectionNetwork.from_yaml(CONFIG), Timetable.from_yaml(CONFIG))


def _etypes(g):
    return {d["etype"] for _, _, d in g.edges(data=True)}


def test_build_has_typed_nodes_and_all_relations():
    g = _builder().build()

    ntypes = {d["ntype"] for _, d in g.nodes(data=True)}
    assert ntypes == {"station", "service"}
    assert g.number_of_nodes() == 3 + 4  # 3 stations + 4 services

    # the full graph carries every cascade relation + the structural connector
    assert {e.value for e in EdgeType} <= _etypes(g)
    assert SERVES in _etypes(g)

    # learned-weight placeholder + named edge features are present
    for _, _, d in g.edges(data=True):
        assert d["weight"] == 1.0
        assert "scheduled_delta_min" in d and "min_turnaround_min" in d


def test_disruption_node_returns_khop_with_all_edge_types():
    gb = _builder()
    gb.build()
    sub = gb.k_hop_subgraph("MGS", k=2)  # OHE failure at MGS

    assert "station:MGS" in sub
    assert sub.number_of_nodes() <= gb.graph.number_of_nodes()
    # all five cascade edge types reachable in the disruption neighborhood
    assert {e.value for e in EdgeType} <= _etypes(sub)


def test_rake_link_carries_turnaround_feature():
    g = _builder().build()
    data = g.get_edge_data("service:12301", "service:12302")
    rake = data[EdgeType.RAKE_LINK.value]
    assert rake["min_turnaround_min"] == 15
    assert rake["scheduled_delta_min"] == 15  # dep 12302@BSB(70) - arr 12301@BSB(55)


def test_unknown_node_raises():
    gb = _builder()
    gb.build()
    try:
        gb.k_hop_subgraph("NOPE")
        assert False, "expected KeyError"
    except KeyError:
        pass
