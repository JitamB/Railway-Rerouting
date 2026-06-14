// REST helpers for the snapshot/drill-down reads (the WS carries the live deltas).
import { API_BASE } from "./ws";

export interface StationView {
  station: string;
  cascade_risk: number;
  delay_interval_min: [number, number];
  why: string;
  incoming_trains: string[];
  mode: string;
  data_age_s: number;
  watermark: string;
}

export interface CorridorHealth {
  zone: string;
  max_risk: number;
  mean_risk: number;
  stations_at_risk: string[];
  status: string; // green | amber | red
  data_age_s: number;
  watermark: string;
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path} -> ${res.status}`);
  return (await res.json()) as T;
}

export const getStation = (code: string) => getJson<StationView>(`/stations/${code}`);
export const getCorridor = (zone: string) => getJson<CorridorHealth>(`/corridor/${zone}`);
