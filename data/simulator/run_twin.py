"""Run the digital twin and print its event stream as a timeline.

    python data/simulator/run_twin.py                          # baseline (on-time) day
    python data/simulator/run_twin.py --scenario ohe_failure --horizon 160

With --scenario, runs the baseline and the disrupted day and prints the delay bloom
(per train/station delta) plus a one-line metric: total passenger delay-minutes injected.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from cascadeguard_sim.engine import SimulationEngine
from cascadeguard_sim.network import SectionNetwork
from cascadeguard_sim.timetable import Timetable

CONFIG = Path(__file__).resolve().parent / "config" / "section.example.yaml"


def _engine(config: str) -> SimulationEngine:
    return SimulationEngine(
        SectionNetwork.from_yaml(config),
        Timetable.from_yaml(config),
        config_path=config,
    )


def _print_timeline(events) -> None:
    print(f"{'t(min)':>7}  {'train':<6} {'stn':<5} {'delay':>6}")
    print("-" * 30)
    for e in events:
        print(f"{e.event_time:7.0f}  {e.train_no:<6} {e.station:<5} {e.delay_min:+6.1f}")


def _print_bloom(baseline, injected, scenario: str) -> None:
    base = {(e.train_no, e.station): e.delay_min for e in baseline}
    print(f"injected scenario: {scenario}")
    print(f"{'t(min)':>7}  {'train':<6} {'stn':<5} {'base':>6} {'now':>6} {'Δ':>6}")
    print("-" * 50)
    total = 0.0
    affected = 0
    for e in injected:
        b = base.get((e.train_no, e.station), 0.0)
        d = e.delay_min - b
        bar = "█" * min(int(e.delay_min), 30)
        print(f"{e.event_time:7.0f}  {e.train_no:<6} {e.station:<5} "
              f"{b:+6.1f} {e.delay_min:+6.1f} {d:+6.1f}  {bar}")
        total += e.delay_min
        affected += 1 if e.delay_min > 0 else 0
    peak = max((e.delay_min for e in injected), default=0.0)
    print("-" * 50)
    print(f"METRIC: {total:.0f} train-delay-min over {affected} affected stop(s); "
          f"peak {peak:.0f} min")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", help="scenario id from the section config (e.g. ohe_failure)")
    ap.add_argument("--horizon", type=float, default=160, help="sim minutes to run")
    ap.add_argument("--config", default=str(CONFIG))
    args = ap.parse_args()

    baseline = list(_engine(args.config).run(horizon_min=args.horizon))

    if not args.scenario:
        print(f"twin baseline: {len(baseline)} events over {args.horizon:.0f} sim-min")
        _print_timeline(baseline)
        return

    eng = _engine(args.config)
    eng.inject(args.scenario)
    injected = list(eng.run(horizon_min=args.horizon))
    print(f"twin: {len(injected)} events over {args.horizon:.0f} sim-min  (regime={eng.regime})")
    _print_bloom(baseline, injected, args.scenario)


if __name__ == "__main__":
    main()
