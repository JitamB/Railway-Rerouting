from cascadeguard_graph.schema import (
    CANONICAL_RELATIONS,
    EDGE_FEATURES,
    NODE_TYPES,
    SERVES,
    SERVICE_FEATURES,
    STATION_FEATURES,
    EdgeType,
)


def test_edge_type_enum_is_the_five_cascade_relations():
    assert {e.value for e in EdgeType} == {
        "block_conflict", "platform_conflict", "rake_link", "crew_link", "loco_link"
    }


def test_canonical_relations_cover_every_edge_type_with_valid_endpoints():
    relation_names = {rel for _, rel, _ in CANONICAL_RELATIONS}
    # every cascade edge type is wired into a canonical relation
    assert {e.value for e in EdgeType} <= relation_names
    # plus the structural connector
    assert SERVES in relation_names
    # endpoints are declared node types
    for src, _, dst in CANONICAL_RELATIONS:
        assert src in NODE_TYPES and dst in NODE_TYPES


def test_feature_lists_are_nonempty_name_tuples():
    for feats in (STATION_FEATURES, SERVICE_FEATURES, EDGE_FEATURES):
        assert feats and all(isinstance(f, str) for f in feats)
