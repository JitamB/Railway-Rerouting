// Colour-coded station nodes (green -> amber -> red), updated by WebSocket deltas. Skeleton.

const card = { border: "1px solid #e5e7eb", borderRadius: 8, padding: 16 } as const;

export function RiskHeatmap() {
  // TODO: Mapbox layer keyed on per-station cascade risk; grey out stale nodes.
  return (
    <section style={{ ...card, minHeight: 360 }}>
      <h2 style={{ marginTop: 0 }}>Cascade Risk Heatmap</h2>
      <p style={{ color: "#6b7280" }}>
        Mapbox station heatmap (green → amber → red) renders here once the WS feed + Mapbox token
        are wired (Step 28).
      </p>
    </section>
  );
}
