// Background push via expo-notifications (FCM on Android, APNs on iOS).
// Reliable when the app is closed — this carries the proactive re-route alert.
//
// NOTE: remote push was removed from Expo Go in SDK 53. So we **no-op in Expo Go** (the app
// still runs) and only touch expo-notifications in a development / EAS build. The module is
// imported lazily so it never initializes under Expo Go.
import Constants, { ExecutionEnvironment } from "expo-constants";

const isExpoGo = Constants.executionEnvironment === ExecutionEnvironment.StoreClient;

export async function registerPush(): Promise<string | null> {
  if (isExpoGo) {
    console.info("[push] skipped in Expo Go — use a dev build for background push.");
    return null;
  }
  const Device = await import("expo-device");
  if (!Device.isDevice) return null;
  const Notifications = await import("expo-notifications");

  // Foreground delivery: still surface the re-route banner while the app is open.
  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldShowBanner: true,
      shouldShowList: true,
      shouldPlaySound: true,
      shouldSetBadge: false,
    }),
  });

  let { status } = await Notifications.getPermissionsAsync();
  if (status !== "granted") {
    status = (await Notifications.requestPermissionsAsync()).status;
  }
  if (status !== "granted") return null;

  try {
    const projectId = (Constants.expoConfig?.extra as { eas?: { projectId?: string } })?.eas?.projectId;
    const token = await Notifications.getExpoPushTokenAsync(projectId ? { projectId } : undefined);
    // The token→PNR mapping is sent to the backend once the push-registration endpoint lands
    // (services/api); the worker (services/worker) then targets this device. Until then we keep
    // the resolved token here so the foreground/dev-build path is verifiable.
    console.info("[push] expo push token acquired");
    return token.data;
  } catch {
    return null; // no projectId configured yet (EAS) — fine for the QR/dev demo
  }
}

export async function onPushReceived(handler: (notification: unknown) => void): Promise<void> {
  if (isExpoGo) return;
  const Notifications = await import("expo-notifications");
  Notifications.addNotificationReceivedListener(handler as never);
}
