// FCM registration + service-worker push handling (delivers when the app is closed).

export async function registerPush(): Promise<string | null> {
  // TODO: request permission, register SW, return FCM token.
  return null;
}

export function onPushMessage(handler: (payload: unknown) => void): void {
  // TODO: wire FCM onMessage -> handler (render the template-first alert immediately).
  void handler;
}
