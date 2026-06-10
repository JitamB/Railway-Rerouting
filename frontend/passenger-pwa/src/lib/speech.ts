// Microphone capture for regional-language speech input.
// Records audio in the browser (MediaRecorder) and returns the clip; transcription happens
// server-side in the helpline agent's ASR (Bhashini/Whisper), so no language model ships here.

export async function captureSpeech(): Promise<Blob | null> {
  // TODO: getUserMedia -> MediaRecorder -> return recorded audio Blob for upload.
  return null;
}
