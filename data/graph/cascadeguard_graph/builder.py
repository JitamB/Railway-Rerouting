"""Build the heterogeneous dependency graph from timetable + section topology.

Emits a typed multi-relational graph (a networkx ``MultiDiGraph``, HeteroData-compatible: node
types, the relations in ``schema.CANONICAL_RELATIONS``, and named node/edge features). Every
edge carries a ``weight`` placeholder that is fit jointly with the GNN, never hand-set
(audit-02 §3.4). The PyG tensor conversion lives in the ML data module (Step 14); the graph
package stays framework-light.

Inference is event-scoped: ``k_hop_subgraph`` returns only the neighborhood around a disruption,
never a global recompute (audit-04 §10).
"""

from __future__ import annotations

import networkx as nx

from .schema import SERVES, EdgeType

PLATFORM_WINDOW_MIN = 15.0  # services arriving at a station within this gap are platform-coupled
PLACEHOLDER_WEIGHT = 1.0  # learned end-to-end with the GNN


def _stn(code: str) -> str:
    return f"station:{code}"


def _svc(train: str) -> str:
    return f"service:{train}"


class GraphBuilder:
    def __init__(self, network: "object", timetable: "object") -> None:
        self.network = network
        self.timetable = timetable
        self.graph: nx.MultiDiGraph | None = None

    def build(self) -> nx.MultiDiGraph:
        """Return a HeteroData-shaped graph with typed edges and node/edge features."""
        g = nx.MultiDiGraph()
        net, tt = self.network, self.timetable

        # incoming_density = how many services call at the station.
        density: dict[str, int] = {}
        for svc in tt.services():
            for s in svc.sched_arr_min:
                density[s] = density.get(s, 0) + 1

        # station nodes
        for s in net.stations():
            g.add_node(_stn(s.code), ntype="station", platforms=s.platforms,
                       incoming_density=density.get(s.code, 0), regime=0.0)

        # service nodes + structural "serves" edges to each stop
        for svc in tt.services():
            g.add_node(_svc(svc.train_no), ntype="service",
                       n_stops=len(svc.stops), max_delay_min=0.0)
            for stop in svc.stops:
                self._edge(g, _svc(svc.train_no), _stn(stop), SERVES, 0.0, 0.0)

        # block_conflict: adjacent stations (both directions), feature = headway
        for b in net.block_sections():
            self._edge(g, _stn(b.from_station), _stn(b.to_station),
                       EdgeType.BLOCK_CONFLICT.value, b.headway_min, 0.0)
            self._edge(g, _stn(b.to_station), _stn(b.from_station),
                       EdgeType.BLOCK_CONFLICT.value, b.headway_min, 0.0)

        # platform_conflict: services calling at the same station close in time
        for s in net.stations():
            callers = sorted(
                (svc for svc in tt.services() if s.code in svc.sched_arr_min),
                key=lambda v: v.sched_arr_min[s.code],
            )
            for i, a in enumerate(callers):
                for b in callers[i + 1:]:
                    gap = b.sched_arr_min[s.code] - a.sched_arr_min[s.code]
                    if gap <= PLATFORM_WINDOW_MIN:
                        self._edge(g, _svc(a.train_no), _svc(b.train_no),
                                   EdgeType.PLATFORM_CONFLICT.value, gap, 0.0)

        # rake_link: inbound -> outbound on the same physical rake
        for lk in tt.rake_links():
            gap = self._handoff_gap(tt.service(lk.inbound), tt.service(lk.outbound))
            self._edge(g, _svc(lk.inbound), _svc(lk.outbound),
                       EdgeType.RAKE_LINK.value, gap, lk.min_turnaround_min)

        # loco_link / crew_link: resource hand-offs between services
        for lk in tt.loco_links():
            gap = self._handoff_gap(tt.service(lk.from_service), tt.service(lk.to_service))
            self._edge(g, _svc(lk.from_service), _svc(lk.to_service),
                       EdgeType.LOCO_LINK.value, gap, 0.0)
        for lk in tt.crew_links():
            gap = self._handoff_gap(tt.service(lk.from_service), tt.service(lk.to_service))
            self._edge(g, _svc(lk.from_service), _svc(lk.to_service),
                       EdgeType.CREW_LINK.value, gap, 0.0)

        self.graph = g
        return g

    def k_hop_subgraph(self, node: str, k: int = 3) -> nx.MultiDiGraph:
        """Event-scoped subgraph around a disruption (audit-04 §10)."""
        g = self.graph if self.graph is not None else self.build()
        start = self._resolve(g, node)

        und = g.to_undirected(as_view=True)
        seen = {start}
        frontier = {start}
        for _ in range(k):
            nxt = {nb for n in frontier for nb in und.neighbors(n)} - seen
            if not nxt:
                break
            seen |= nxt
            frontier = nxt
        return g.subgraph(seen).copy()

    @staticmethod
    def _resolve(g: nx.MultiDiGraph, node: str) -> str:
        for cand in (node, _stn(node), _svc(node)):
            if cand in g:
                return cand
        raise KeyError(f"node {node!r} not in graph")

    @staticmethod
    def _handoff_gap(from_svc: "object", to_svc: "object") -> float:
        # If the outbound starts where the inbound ended, the scheduled turnaround gap.
        origin, terminus = to_svc.stops[0], from_svc.stops[-1]
        if origin == terminus:
            return to_svc.sched_dep_min.get(origin, 0.0) - from_svc.sched_arr_min.get(terminus, 0.0)
        return 0.0

    @staticmethod
    def _edge(g, src, dst, etype, scheduled_delta_min, min_turnaround_min) -> None:
        g.add_edge(src, dst, key=etype, etype=etype, weight=PLACEHOLDER_WEIGHT,
                   scheduled_delta_min=scheduled_delta_min, min_turnaround_min=min_turnaround_min)
