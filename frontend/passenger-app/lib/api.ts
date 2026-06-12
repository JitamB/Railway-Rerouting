// REST client to the CascadeGuard FastAPI backend (services/api).
// Base URL comes from app.json -> extra.apiBaseUrl (per-environment).
import Constants from "expo-constants";

const BASE_URL: string =
  (Constants.expoConfig?.extra as { apiBaseUrl?: string })?.apiBaseUrl ?? "http://localhost:8000";

export async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`);
  return res.json() as Promise<T>;
}

export async function postHelplineText(passengerId: string, text: string): Promise<unknown> {
  // TODO: POST /helpline/chat with text.
  void passengerId;
  void text;
  return null;
}

export async function postHelplineAudio(audio: Blob | { uri: string }): Promise<unknown> {
  // TODO: multipart POST /helpline/chat with the recorded clip (server-side ASR).
  void audio;
  return null;
}
