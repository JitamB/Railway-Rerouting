// Cascade-chain visualisation with the per-hop "why". Skeleton.
// e.g. "12301 -> Patna Jn -> Mughal Sarai (71%) -> Varanasi (54%)".

export function CascadeChain() {
  // TODO: render the propagation path + GNNExplainer attribution per hop.
  return (
    <section style={{ border: "1px solid #e5e7eb", borderRadius: 8, padding: 16 }}>
      <h2 style={{ marginTop: 0 }}>Cascade Chain</h2>
      <p style={{ color: "#6b7280" }}>
        e.g. 12301 → Patna Jn → Mughal Sarai (71%) → Varanasi (54%), with the per-hop “why”.
      </p>
    </section>
  );
}
