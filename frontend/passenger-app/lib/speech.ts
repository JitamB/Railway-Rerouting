// Microphone capture for regional-language speech input (expo-av).
// Records a clip on-device and returns its URI; transcription happens server-side in the
// helpline agent's ASR (Bhashini/Whisper), so no language model ships in the app.
import { Audio } from "expo-av";

export async function captureSpeech(): Promise<{ uri: string } | null> {
  // TODO: request mic permission, record via Audio.Recording, stop, return the file URI.
  await Audio.requestPermissionsAsync();
  return null;
}
