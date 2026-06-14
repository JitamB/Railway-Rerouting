// Control-room design tokens. Dark, high-contrast, with the green→amber→red risk spine reading
// clearly at a glance across a corridor. Grey is reserved for "no/stale data" — never let an
// absence of data read as "safe".
export const c = {
  bg: "#0A0F1E",
  panel: "#111A30",
  panelAlt: "#0D1424",
  border: "#22304E",
  borderSoft: "#1A2540",
  text: "#E8EEF9",
  textMute: "#9FB0CC",
  textFaint: "#5E6F8F",
  brand: "#818CF8",
  brandDim: "#4F46E5",
  green: "#22C55E",
  amber: "#F59E0B",
  red: "#F0454F",
  grey: "#4B5A78",
} as const;

// The demo corridor (PNBE → MGS → BSB), with display names and a 0..1 position along the line.
export const CORRIDOR: { code: string; name: string; x: number }[] = [
  { code: "PNBE", name: "Patna Jn", x: 0.1 },
  { code: "MGS", name: "Mughal Sarai", x: 0.5 },
  { code: "BSB", name: "Varanasi", x: 0.9 },
];

export interface RiskTone {
  fill: string;
  glow: string;
  label: string;
  level: "unknown" | "low" | "elevated" | "high";
}

// risk is 0..1, or null/undefined when we have no fresh reading for this node.
export function riskTone(risk: number | null | undefined): RiskTone {
  if (risk == null) return { fill: c.grey, glow: "rgba(75,90,120,0.0)", label: "No data", level: "unknown" };
  if (risk >= 0.66) return { fill: c.red, glow: "rgba(240,69,79,0.55)", label: "High", level: "high" };
  if (risk >= 0.33) return { fill: c.amber, glow: "rgba(245,158,11,0.45)", label: "Elevated", level: "elevated" };
  return { fill: c.green, glow: "rgba(34,197,94,0.40)", label: "Low", level: "low" };
}
