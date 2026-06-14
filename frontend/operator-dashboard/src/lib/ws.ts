// WebSocket client for /ws/live. Consumes per-station cascade *deltas* (not full state), then a
// completion marker. The API closes the socket after a snapshot, so we auto-reconnect to keep the
// control-room view live; the disposer stops reconnecting on unmount.

const env = (import.meta as unknown as { env?: Record<string, string> }).env;
export const API_BASE: string = env?.VITE_API_BASE ?? "http://localhost:8000";
export const WS_URL: string = `${API_BASE.replace(/^http/, "ws")}/ws/live`;

export interface CascadeDelta {
  station: string;
  cascade_risk: number;
  delay_interval_min: [number, number];
  mode: string;
  data_age_s: number;
}

export type FeedStatus = "connecting" | "live" | "offline";

export interface FeedHandlers {
  onDelta: (delta: CascadeDelta) => void;
  onStatus: (status: FeedStatus) => void;
  onComplete?: (count: number) => void;
}

export function connectLiveFeed(handlers: FeedHandlers): () => void {
  let ws: WebSocket | null = null;
  let disposed = false;
  let retry: ReturnType<typeof setTimeout> | undefined;

  function open() {
    if (disposed) return;
    handlers.onStatus("connecting");
    ws = new WebSocket(WS_URL);

    ws.onopen = () => handlers.onStatus("live");
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data as string);
        if (msg.type === "delta") handlers.onDelta(msg as CascadeDelta);
        else if (msg.type === "complete") handlers.onComplete?.(msg.count);
      } catch {
        /* ignore malformed frame */
      }
    };
    ws.onerror = () => ws?.close();
    ws.onclose = () => {
      if (disposed) return;
      handlers.onStatus("offline");
      retry = setTimeout(open, 2500); // keep the corridor view live; re-pull the snapshot
    };
  }

  open();
  return () => {
    disposed = true;
    if (retry) clearTimeout(retry);
    ws?.close();
  };
}
