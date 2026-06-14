// REST client to the CascadeGuard FastAPI backend (services/api).
// Base URL comes from app.json -> extra.apiBaseUrl (per-environment).
import Constants from "expo-constants";

const BASE_URL: string =
  (Constants.expoConfig?.extra as { apiBaseUrl?: string })?.apiBaseUrl ?? "http://localhost:8000";

export { BASE_URL };

// ---- response contracts (mirror services/api/cascadeguard_api) -----------------------------
export interface CascadeStation {
  station: string;
  cascade_risk: number;
  delay_mean_min: number;
  delay_interval_min: [number, number];
  why: string;
  mode: string;
  data_age_s: number;
}

export interface CascadeResponse {
  train_no: string;
  stations: CascadeStation[];
  mode: string;
  data_age_s: number;
  watermark: string;
}

export interface RerouteOption {
  train_no: string;
  platform: string;
  departs: string;
  arrives_dest: string;
  seats_status: string; // "AVL 69" | "WL .." | "FULL" ...
}

export interface RerouteResponse {
  pnr: string;
  current_risk: number;
  options: RerouteOption[];
  guidance: string;
  watermark: string;
}

export interface HelplineReply {
  case_id?: string;
  text?: string;
  authority?: string;
  status?: string;
}

export interface QuerySummary {
  case_id: string;
  category: string;
  department: string;
  summary: string;
  status: string; // open | in_progress | resolved | rejected
  created_at: string;
  updated_at: string;
}

// ---- low-level helpers ----------------------------------------------------------------------
export async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) throw new Error(`GET ${path} -> ${res.status}`);
  return res.json() as Promise<T>;
}

async function postJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, { method: "POST" });
  if (!res.ok) throw new Error(`POST ${path} -> ${res.status}`);
  return res.json() as Promise<T>;
}

// ---- typed endpoints ------------------------------------------------------------------------
export const getCascade = (trainNo: string) => getJson<CascadeResponse>(`/cascade/${trainNo}`);

export const getReroute = (pnr: string) =>
  postJson<RerouteResponse>(`/reroute?pnr=${encodeURIComponent(pnr)}`);

export async function getQueries(passengerId: string): Promise<QuerySummary[]> {
  // The helpline/queries service is the Stage-9 track; tolerate a not-yet-implemented body.
  const data = await getJson<QuerySummary[] | null>(`/queries?passenger_id=${encodeURIComponent(passengerId)}`);
  return Array.isArray(data) ? data : [];
}

export async function postHelplineText(passengerId: string, text: string): Promise<HelplineReply> {
  const q = `passenger_id=${encodeURIComponent(passengerId)}&text=${encodeURIComponent(text)}`;
  const data = await postJson<HelplineReply | null>(`/helpline/chat?${q}`);
  return data ?? {};
}

export async function postHelplineAudio(
  passengerId: string,
  audio: { uri: string },
  language?: string,
): Promise<HelplineReply> {
  const form = new FormData();
  form.append("audio", { uri: audio.uri, name: "speech.m4a", type: "audio/m4a" } as unknown as Blob);
  const q = `passenger_id=${encodeURIComponent(passengerId)}${language ? `&language=${language}` : ""}`;
  const res = await fetch(`${BASE_URL}/helpline/chat?${q}`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`POST /helpline/chat -> ${res.status}`);
  const data = (await res.json()) as HelplineReply | null;
  return data ?? {};
}
