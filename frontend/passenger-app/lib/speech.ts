// Microphone capture for regional-language speech input (expo-audio).
// Records a clip on-device; transcription happens server-side in the helpline agent's ASR
// (Bhashini/Whisper), so no language model ships in the app. The actual recording uses the
// `useAudioRecorder` hook inside HelplineChat; this helper handles the mic permission.
import { requestRecordingPermissionsAsync } from "expo-audio";

export async function requestMicPermission(): Promise<boolean> {
  const res = await requestRecordingPermissionsAsync();
  return res.granted;
}
