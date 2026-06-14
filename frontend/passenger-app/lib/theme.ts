// Shared design tokens for the passenger app — one source of truth for colour, spacing, radius,
// shadow and type, so every screen looks like one product. Risk colours (green/amber/red) are
// the visual spine: they map cascade probability to a calm, legible status the passenger trusts.
import { Platform, type TextStyle, type ViewStyle } from "react-native";

export const colors = {
  brand: "#312E81", // indigo-900 — calm, official, "transit authority"
  brandSoft: "#4F46E5",
  brandTint: "#EEF2FF",
  bg: "#F1F5F9",
  surface: "#FFFFFF",
  surfaceAlt: "#F8FAFC",
  border: "#E2E8F0",
  borderStrong: "#CBD5E1",
  text: "#0F172A",
  textMute: "#475569",
  textFaint: "#94A3B8",
  // risk spine
  green: "#15803D",
  greenBg: "#DCFCE7",
  amber: "#B45309",
  amberBg: "#FEF3C7",
  red: "#B91C1C",
  redBg: "#FEE2E2",
  white: "#FFFFFF",
} as const;

export const radius = { sm: 8, md: 12, lg: 16, xl: 22, pill: 999 } as const;

// 4-pt spacing scale.
export const space = (n: number): number => n * 4;

export const shadow = {
  card: Platform.select<ViewStyle>({
    ios: {
      shadowColor: "#0F172A",
      shadowOffset: { width: 0, height: 6 },
      shadowOpacity: 0.08,
      shadowRadius: 16,
    },
    android: { elevation: 3 },
    default: {},
  })!,
  raised: Platform.select<ViewStyle>({
    ios: {
      shadowColor: "#312E81",
      shadowOffset: { width: 0, height: 10 },
      shadowOpacity: 0.18,
      shadowRadius: 24,
    },
    android: { elevation: 8 },
    default: {},
  })!,
} as const;

export const type = {
  display: { fontSize: 30, fontWeight: "800", letterSpacing: -0.5, color: colors.text } as TextStyle,
  h1: { fontSize: 22, fontWeight: "800", letterSpacing: -0.3, color: colors.text } as TextStyle,
  h2: { fontSize: 17, fontWeight: "700", color: colors.text } as TextStyle,
  body: { fontSize: 15, fontWeight: "500", color: colors.textMute, lineHeight: 22 } as TextStyle,
  label: { fontSize: 12, fontWeight: "700", letterSpacing: 0.6, color: colors.textFaint } as TextStyle,
  mono: {
    fontFamily: Platform.select({ ios: "Menlo", android: "monospace", default: "monospace" }),
    fontWeight: "700",
    color: colors.text,
  } as TextStyle,
} as const;

export interface RiskStyle {
  fg: string;
  bg: string;
  label: string; // "Low" | "Elevated" | "High"
  level: "low" | "elevated" | "high";
}

// Cascade probability (0..1) -> the calm/watch/act colour band the whole UI keys on.
export function riskStyle(risk: number): RiskStyle {
  if (risk >= 0.66) return { fg: colors.red, bg: colors.redBg, label: "High", level: "high" };
  if (risk >= 0.33) return { fg: colors.amber, bg: colors.amberBg, label: "Elevated", level: "elevated" };
  return { fg: colors.green, bg: colors.greenBg, label: "Low", level: "low" };
}
