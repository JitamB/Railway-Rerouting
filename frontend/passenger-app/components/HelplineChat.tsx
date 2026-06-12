// Chat UI for the helpline: text input + mic for regional-language speech. Skeleton.
// Speech is captured via lib/speech.ts (expo-av) and sent to POST /helpline/chat (backend ASR).
// The agent reply shows the opened case id, routed authority, and status.
import { View, Button } from "react-native";
import { captureSpeech } from "../lib/speech";
import { postHelplineAudio } from "../lib/api";

export function HelplineChat() {
  async function onMic() {
    const clip = await captureSpeech();
    if (clip) await postHelplineAudio(clip);
    // TODO: render the agent reply + opened case.
  }

  return (
    <View accessibilityLabel="helpline-chat">
      {/* TODO: message list + text input */}
      <Button title="🎤 Speak" onPress={onMic} />
    </View>
  );
}
