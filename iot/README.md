# `iot/` — Edge Node Layer (Phase-2 schematic · OPTIONAL)

> **Off the critical path.** Present this as a credible Phase-2 schematic with a real protocol
> stack and BOM — *not* a flaky breadboard. A clean schematic earns more than a half-working
> demo ([audit-03 §8](../docs/audit-03-worth-winning-upgrades.md)).

## What it is (and is NOT)
A lone node **cannot** compute the network cascade — that needs network-wide state
([audit-02 §3.5](../docs/audit-02-architecture-deep-dive.md)). So the correct architecture is
**sense at the edge, reason centrally**:
- **Edge node:** local sensing + local single-node inference ("is *my* platform about to
  conflict?") + **feature forwarding** upstream.
- **Centre:** the network cascade is computed centrally and pushed back down.

## Specifics (domain literacy matters)
| Concern | Choice |
|---|---|
| Protocol | **MQTT over LoRaWAN** for constrained nodes; NB-IoT cellular fallback |
| Ground-truth sensing | **Axle counters / track circuits** for block occupancy (not vague ultrasonic) |
| Edge inference | **ONNX Runtime** on Raspberry Pi 5 / Jetson Nano-class node |
| Time | NTP-disciplined clocks; reject events implying impossible latency (audit-04 §9) |

## Layout
| Path | Role |
|---|---|
| `firmware/` | ESP32 / Pi node firmware (MQTT publisher, ONNX local inference) |
| `hardware/` | Junction sensor-unit schematic + BOM (ESP32, LoRa radio, axle-counter interface, GSM redundancy) |
