"""Datamodule: assembles training windows from twin events + the dependency graph.

Pairs event-time delay sequences with the heterogeneous subgraph. Mixes a clean baseline with
**simulator-injected rare events** (OHE-style closures, fog regimes) so the model sees the
shape of derailment/fog cascades it can't learn from normal logs (audit-04 §2/§6).

Design choice that makes the rake-link ablation clean: the temporal **delay signal lives on
service (train) nodes**; station nodes carry only capacity/topology features and never feed
back into services. So cross-train propagation must traverse the service-service edges
(rake/crew/loco/platform) — exactly what the ablation probes. The outbound rake (12302) has no
observed delay of its own at the cutoff, so its delay is knowable only via the rake-link.
"""

from __future__ import annotations

import random

import numpy as np
import torch
from torch_geometric.data import HeteroData
from torch_geometric.loader import DataLoader

from cascadeguard_graph.builder import GraphBuilder
from cascadeguard_sim.engine import SimulationEngine
from cascadeguard_sim.network import SectionNetwork
from cascadeguard_sim.timetable import Timetable

from cascadeguard_ml.spec import (
    DEFAULT_SECTION_CONFIG,
    HORIZON,
    OBS_CUTOFF,
    OBS_WINDOW,
    RAKE_LINK_RELATION,
    RELATIONS,
    RISK_THRESHOLD,
    T,
)


def _nx_graph(section_config: str):
    net = SectionNetwork.from_yaml(section_config)
    tt = Timetable.from_yaml(section_config)
    return GraphBuilder(net, tt).build(), net, tt


def _index_maps(g):
    stations = sorted(n for n, d in g.nodes(data=True) if d["ntype"] == "station")
    services = sorted(n for n, d in g.nodes(data=True) if d["ntype"] == "service")
    return (
        {n: i for i, n in enumerate(stations)},
        {n: i for i, n in enumerate(services)},
        stations,
        services,
    )


def _edge_index_dict(g, st_idx, sv_idx, ablate_rake_link: bool):
    idx = {"station": st_idx, "service": sv_idx}
    buckets: dict[tuple, list] = {}
    for u, v, d in g.edges(data=True):
        etype = d["etype"]
        if etype == "serves":
            # flip to station->service so stations feed capacity context, not delay
            rel, src, dst = ("station", "serves", "service"), v, u
        else:
            rel, src, dst = (g.nodes[u]["ntype"], etype, g.nodes[v]["ntype"]), u, v
        if rel not in RELATIONS:
            continue
        if ablate_rake_link and rel == RAKE_LINK_RELATION:
            continue
        pairs = buckets.setdefault(rel, [[], []])
        pairs[0].append(idx[rel[0]][src])
        pairs[1].append(idx[rel[2]][dst])
    return {rel: torch.tensor(pairs, dtype=torch.long) for rel, pairs in buckets.items()}


def _run_twin(net, tt, *, station=None, start=0.0, duration=0.0, fog=False):
    eng = SimulationEngine(net, tt)
    if station is not None:
        eng.station_closed[station] = (start, start + duration)
    if fog:
        eng.running_time_factor = 1.3
        eng.regime = "fog"
    return list(eng.run(horizon_min=HORIZON)), eng.regime


def _service_history(events, train_no):
    """Delay trajectory of a train over [cutoff-window, cutoff], T samples (0 before first event)."""
    arrivals = sorted(((e.event_time, e.delay_min) for e in events if e.train_no == train_no))
    times = np.linspace(OBS_CUTOFF - OBS_WINDOW, OBS_CUTOFF, T)
    hist = np.zeros(T, dtype=np.float32)
    for i, t in enumerate(times):
        seen = [d for (et, d) in arrivals if et <= t]
        hist[i] = seen[-1] if seen else 0.0
    return hist


def _peak_delay(events, train_no):
    delays = [e.delay_min for e in events if e.train_no == train_no]
    return max(delays) if delays else 0.0


def make_sample(net, tt, g, st_idx, sv_idx, services, *, station, start, duration, fog,
                ablate_rake_link=False) -> HeteroData:
    events, regime = _run_twin(net, tt, station=station, start=start, duration=duration, fog=fog)
    regime_code = 1.0 if regime != "normal" else 0.0

    data = HeteroData()

    # station nodes: capacity/topology only (no delay signal) -> prediction sinks
    station_codes = sorted(st_idx, key=lambda n: st_idx[n])
    st_x = []
    for code in station_codes:
        nd = g.nodes[code]
        st_x.append([nd["platforms"] / 10.0, nd["incoming_density"] / 4.0, regime_code])
    data["station"].x = torch.tensor(st_x, dtype=torch.float32)
    data["station"].history = torch.zeros((len(station_codes), T), dtype=torch.float32)

    # service nodes: carry the observed delay history + the cascade targets
    sv_hist, sv_x, y_delay = [], [], []
    for node in sorted(sv_idx, key=lambda n: sv_idx[n]):
        train_no = node.split(":", 1)[1]
        sv_hist.append(_service_history(events, train_no))
        sv_x.append([g.nodes[node]["n_stops"] / 3.0, regime_code])
        y_delay.append(_peak_delay(events, train_no))
    data["service"].history = torch.tensor(np.array(sv_hist), dtype=torch.float32)
    data["service"].x = torch.tensor(sv_x, dtype=torch.float32)
    yd = torch.tensor(y_delay, dtype=torch.float32)
    data["service"].y_delay = yd
    data["service"].y_risk = (yd > RISK_THRESHOLD).float()

    for rel, ei in _edge_index_dict(g, st_idx, sv_idx, ablate_rake_link).items():
        data[rel].edge_index = ei
    return data


class CascadeDataModule:
    """Generates (history, subgraph, target) samples from randomized twin disruptions."""

    def __init__(
        self,
        section_config: str = DEFAULT_SECTION_CONFIG,
        events_source: str = "twin",
        window_min: int = 120,
        *,
        n_samples: int = 256,
        seed: int = 0,
        ablate_rake_link: bool = False,
        fog_prob: float = 0.3,
    ) -> None:
        self.section_config = section_config
        self.ablate_rake_link = ablate_rake_link
        self.fog_prob = fog_prob
        self.g, self.net, self.tt = _nx_graph(section_config)
        self.st_idx, self.sv_idx, self.stations, self.services = _index_maps(self.g)

        rng = random.Random(seed)
        samples = [self._random_sample(rng) for _ in range(n_samples)]
        n_val = max(1, int(0.15 * n_samples))
        self._test = samples[:n_val]
        self._val = samples[n_val:2 * n_val]
        self._train = samples[2 * n_val:]

    def _random_sample(self, rng: random.Random) -> HeteroData:
        disrupt = rng.random() < 0.85
        kw = dict(station=None, start=0.0, duration=0.0, fog=rng.random() < self.fog_prob)
        if disrupt:
            # MGS OHE closure that clears before the observation cutoff, so the inbound's delay
            # is observed and the rake cascade to the (not-yet-departed) outbound is genuinely
            # predictable — and reachable only through the rake-link. This is the headline scenario.
            kw.update(station="MGS", start=rng.uniform(28.0, 38.0), duration=rng.uniform(10.0, 22.0))
        return make_sample(self.net, self.tt, self.g, self.st_idx, self.sv_idx, self.services,
                           ablate_rake_link=self.ablate_rake_link, **kw)

    def train_dataloader(self, batch_size: int = 32):
        return DataLoader(self._train, batch_size=batch_size, shuffle=True)

    def val_dataloader(self, batch_size: int = 32):
        return DataLoader(self._val, batch_size=batch_size)

    def test_dataloader(self, batch_size: int = 32):
        return DataLoader(self._test, batch_size=batch_size)

    def demo_sample(self, station: str, *, start: float = 30.0, duration: float = 30.0,
                    fog: bool = False) -> HeteroData:
        """A single deterministic disruption sample for inference at ``station``."""
        return make_sample(self.net, self.tt, self.g, self.st_idx, self.sv_idx, self.services,
                           station=station, start=start, duration=duration, fog=fog,
                           ablate_rake_link=self.ablate_rake_link)
