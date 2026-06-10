// Chat UI for the helpline: text input + mic for regional-language speech. Skeleton.
// Speech is captured via lib/speech.ts and sent to POST /helpline/chat (backend ASR).
// The agent reply shows the opened case id, routed authority, and status.
import { captureSpeech } from "../lib/speech";

export function HelplineChat() {
  async function onMic() {
    const audio = await captureSpeech();
    // TODO: POST audio to /helpline/chat; render reply + opened case.
    void audio;
  }

  return (
    <section aria-label="helpline-chat">
      {/* TODO: message list, text input, send button */}
      <button type="button" onClick={onMic} aria-label="speak">
        🎤 Speak
      </button>
    </section>
  );
}
