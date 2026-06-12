// Background push via expo-notifications (FCM on Android, APNs on iOS).
// Reliable when the app is closed — this carries the proactive re-route alert.
import * as Notifications from "expo-notifications";
import * as Device from "expo-device";

export async function registerPush(): Promise<string | null> {
  if (!Device.isDevice) return null;
  // TODO: request permission, get Expo push token, send it to the backend for this PNR.
  const { status } = await Notifications.getPermissionsAsync();
  void status;
  return null;
}

export function onPushReceived(handler: (n: Notifications.Notification) => void): void {
  // TODO: render the template-first alert immediately on receipt.
  Notifications.addNotificationReceivedListener(handler);
}
