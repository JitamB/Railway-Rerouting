// WebSocket client for /ws/live. Consumes cascade-risk deltas, not full state.

export function connectLiveFeed(onDelta: (delta: unknown) => void): WebSocket | null {
  // TODO: open WS to services/api /ws/live and forward deltas to onDelta.
  void onDelta;
  return null;
}
