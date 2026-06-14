"""Headless end-to-end demo of the worker pipeline (Step 25 verify + 🎯 checkpoint).

Streams events from the digital twin under a disruption scenario, picks the triggering delay at
the disruption station, and walks the full pipeline — inference -> trigger -> re-route ->
template alert (+ optional async LLM) -> push — printing each stage and the final push id. This
shows "a twin-injected delay flows all the way to a push, all on the twin."

    python services/worker/run_pipeline.py --scenario ohe_failure --station MGS

Add ``--llm`` to enrich the prose via Claude (needs ANTHROPIC_API_KEY; falls back to the
template otherwise).
"""

from __future__ import annotations

import argparse

from cascadeguard_ingest.adapters.twin_adapter import TwinAdapter
from cascadeguard_reroute.routing import DEFAULT_SECTION_CONFIG

from cascadeguard_worker.degradation import select_mode, watermark
from cascadeguard_worker.pipeline import process_event


def _trigger_event(scenario: str, station: str) -> dict:
    """The most-delayed event at the disruption station — the signal that starts the pipeline."""
    events = list(TwinAdapter(DEFAULT_SECTION_CONFIG, scenario=scenario).stream())
    at_station = [e for e in events if e["station"] == station and e["delay_min"] > 0]
    if not at_station:
        raise SystemExit(f"No delayed event at {station} under scenario '{scenario}'.")
    return max(at_station, key=lambda e: e["delay_min"])


def main() -> None:
    ap = argparse.ArgumentParser(description="Run the CascadeGuard worker pipeline on the twin.")
    ap.add_argument("--scenario", default="ohe_failure")
    ap.add_argument("--station", default="MGS", help="Disruption station")
    ap.add_argument("--llm", action="store_true", help="Enrich prose via Claude (needs API key)")
    args = ap.parse_args()

    event = _trigger_event(args.scenario, args.station)
    print(f"\n● twin event   train {event['train_no']} @ {event['station']}  "
          f"delay={event['delay_min']:.1f} min  src={event['source']}  ({event['event_time']})")

    client = None
    if args.llm:
        from cascadeguard_llm.client import LlmClient
        client = LlmClient()

    result = process_event(event, llm_client=client)

    print(f"● degradation  mode={result['mode']}  ({result['watermark']})")
    if "dest_station" in result:
        print(f"● inference    dest {result['dest_station']}  risk={result['dest_risk']:.2f}  "
              f"delay={result['dest_delay_min']} min  interval={result['dest_interval_min']}")
        print(f"               why: {result['why']}")
    print(f"● trigger      notified={result['notified']}  ({result['reason']})")
    if result["notified"]:
        if "chosen" in result:
            print(f"● re-route     chosen {result['chosen']}" + (f"  band={result['band']}" if "band" in result else ""))
        print(f"● alert        {result['alert']}")
        print(f"● push         {result['push_id']}")

    print("\nDegradation ladder (feed staleness -> mode):")
    for age in (30, 300, 900):
        print(f"  {age:>4}s old -> {select_mode(age).value:<14} ({watermark(age)})")
    print()


if __name__ == "__main__":
    main()
