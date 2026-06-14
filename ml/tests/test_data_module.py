import torch

from cascadeguard_ml.training.data_module import (
    RAKE_LINK_RELATION,
    T,
    CascadeDataModule,
)


def test_batch_has_aligned_history_subgraph_target():
    dm = CascadeDataModule(n_samples=40, seed=1)
    batch = next(iter(dm.train_dataloader(batch_size=8)))

    sv = batch["service"]
    # history (temporal), subgraph (edges), target (labels) all present and aligned
    n_service = sv.history.size(0)
    assert sv.history.shape == (n_service, T)
    assert sv.x.shape[0] == n_service
    assert sv.y_delay.shape == (n_service,)
    assert sv.y_risk.shape == (n_service,)
    assert n_service % 4 == 0  # 4 services per graph

    # all message-passing relations carry edges in the batch
    rels = set(batch.edge_index_dict.keys())
    assert RAKE_LINK_RELATION in rels
    assert ("station", "block_conflict", "station") in rels
    assert ("station", "serves", "service") in rels  # flipped: stations feed services


def test_targets_span_easy_and_tail_events():
    dm = CascadeDataModule(n_samples=120, seed=2)
    all_delays = torch.cat([s["service"].y_delay for s in dm._train])
    assert (all_delays == 0).any()        # baseline / unaffected trains
    assert (all_delays > 15).any()        # large cascades (the tail)
    assert (all_delays > 0).float().mean() > 0.1


def test_ablation_removes_only_rake_link():
    full = CascadeDataModule(n_samples=8, seed=3)
    ablated = CascadeDataModule(n_samples=8, seed=3, ablate_rake_link=True)
    assert RAKE_LINK_RELATION in next(iter(full.train_dataloader())).edge_index_dict
    assert RAKE_LINK_RELATION not in next(iter(ablated.train_dataloader())).edge_index_dict
    # everything else survives
    assert ("service", "loco_link", "service") in next(iter(ablated.train_dataloader())).edge_index_dict


def test_outbound_rake_has_no_observed_delay_at_cutoff():
    # 12302 hasn't departed by the cutoff -> zero history -> only the rake-link can explain its delay
    dm = CascadeDataModule(n_samples=4, seed=4)
    sample = dm.demo_sample("MGS", start=30, duration=30)
    i_12302 = dm.sv_idx["service:12302"]
    assert torch.count_nonzero(sample["service"].history[i_12302]) == 0
    assert sample["service"].y_delay[i_12302] > 0  # but it does get delayed (via the rake link)
