// Chat UI for the helpline: type or speak in a regional language. Speech is recorded on-device
// (expo-audio) and uploaded to POST /helpline/chat — transcription/NMT happen server-side
// (Bhashini/Whisper), so no language model ships in the app. The agent reply shows the opened
// case id, the routed authority, and a status badge. The grievance service is the Stage-9 track;
// until it returns a body, the UI shows an honest "connecting you to an agent" placeholder.
import { useRef, useState } from "react";
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { RecordingPresets, setAudioModeAsync, useAudioRecorder } from "expo-audio";
import { postHelplineAudio, postHelplineText, type HelplineReply } from "../lib/api";
import { requestMicPermission } from "../lib/speech";
import { colors, radius, shadow, space } from "../lib/theme";

const PASSENGER_ID = "demo-passenger";

const LANGS = [
  { code: "en", label: "EN" },
  { code: "hi", label: "हिं" },
  { code: "bn", label: "বাং" },
  { code: "ta", label: "தமி" },
  { code: "te", label: "తెల" },
  { code: "mr", label: "मरा" },
];

interface Msg {
  id: number;
  from: "me" | "agent";
  text: string;
  reply?: HelplineReply;
}

const STATUS_TONE: Record<string, { fg: string; bg: string }> = {
  open: { fg: colors.amber, bg: colors.amberBg },
  in_progress: { fg: colors.brandSoft, bg: colors.brandTint },
  resolved: { fg: colors.green, bg: colors.greenBg },
  rejected: { fg: colors.red, bg: colors.redBg },
};

export function HelplineChat() {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [draft, setDraft] = useState("");
  const [lang, setLang] = useState("en");
  const [busy, setBusy] = useState(false);
  const [recording, setRecording] = useState(false);
  const scrollRef = useRef<ScrollView>(null);
  const recorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);

  const nextId = useRef(1);
  function push(m: Omit<Msg, "id">) {
    setMsgs((prev) => [...prev, { ...m, id: nextId.current++ }]);
    requestAnimationFrame(() => scrollRef.current?.scrollToEnd({ animated: true }));
  }

  function showReply(reply: HelplineReply) {
    push({
      from: "agent",
      text: reply.text || "Connecting you to a support agent — your query has been logged.",
      reply: reply.case_id ? reply : undefined,
    });
  }

  async function sendText() {
    const text = draft.trim();
    if (!text || busy) return;
    setDraft("");
    push({ from: "me", text });
    setBusy(true);
    try {
      showReply(await postHelplineText(PASSENGER_ID, text));
    } catch {
      push({ from: "agent", text: "Couldn't reach the helpline service. Please try again." });
    } finally {
      setBusy(false);
    }
  }

  async function toggleMic() {
    if (recording) {
      setRecording(false);
      setBusy(true);
      try {
        await recorder.stop();
        const uri = recorder.uri;
        push({ from: "me", text: "🎤 Voice message sent" });
        if (uri) showReply(await postHelplineAudio(PASSENGER_ID, { uri }, lang));
      } catch {
        push({ from: "agent", text: "Recording failed — you can type your query instead." });
      } finally {
        setBusy(false);
      }
      return;
    }
    const granted = await requestMicPermission();
    if (!granted) {
      push({ from: "agent", text: "Microphone permission is needed to speak your query." });
      return;
    }
    try {
      await setAudioModeAsync({ allowsRecording: true, playsInSilentMode: true });
      await recorder.prepareToRecordAsync();
      recorder.record();
      setRecording(true);
    } catch {
      push({ from: "agent", text: "Couldn't start recording — you can type your query instead." });
    }
  }

  return (
    <View style={styles.wrap}>
      {/* language selector */}
      <View style={styles.langRow}>
        {LANGS.map((l) => (
          <TouchableOpacity
            key={l.code}
            onPress={() => setLang(l.code)}
            style={[styles.langChip, lang === l.code && styles.langChipActive]}
            activeOpacity={0.8}
          >
            <Text style={[styles.langText, lang === l.code && styles.langTextActive]}>{l.label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView ref={scrollRef} style={styles.thread} contentContainerStyle={styles.threadContent}>
        {msgs.length === 0 && (
          <View style={styles.intro}>
            <Ionicons name="chatbubbles-outline" size={32} color={colors.textFaint} />
            <Text style={styles.introText}>
              Ask about your delay, a refund, security, or cleanliness — type or tap the mic and
              speak in your language.
            </Text>
          </View>
        )}
        {msgs.map((m) => (
          <View key={m.id} style={[styles.bubbleRow, m.from === "me" ? styles.rowMe : styles.rowAgent]}>
            <View style={[styles.bubble, m.from === "me" ? styles.bubbleMe : styles.bubbleAgent, shadow.card]}>
              <Text style={[styles.bubbleText, m.from === "me" && styles.bubbleTextMe]}>{m.text}</Text>
              {m.reply && (
                <View style={styles.caseBox}>
                  <Text style={styles.caseId}>Case {m.reply.case_id}</Text>
                  <View style={styles.caseMeta}>
                    {!!m.reply.authority && <Text style={styles.caseAuthority}>→ {m.reply.authority}</Text>}
                    {!!m.reply.status && (
                      <View style={[styles.statusBadge, { backgroundColor: (STATUS_TONE[m.reply.status] ?? STATUS_TONE.open).bg }]}>
                        <Text style={[styles.statusText, { color: (STATUS_TONE[m.reply.status] ?? STATUS_TONE.open).fg }]}>
                          {m.reply.status.replace("_", " ")}
                        </Text>
                      </View>
                    )}
                  </View>
                </View>
              )}
            </View>
          </View>
        ))}
        {busy && <ActivityIndicator color={colors.brand} style={{ marginTop: space(2) }} />}
      </ScrollView>

      {/* composer */}
      <View style={styles.composer}>
        <TextInput
          style={styles.composerInput}
          value={draft}
          onChangeText={setDraft}
          placeholder="Type your message…"
          placeholderTextColor={colors.textFaint}
          multiline
          onSubmitEditing={sendText}
        />
        <TouchableOpacity
          onPress={toggleMic}
          style={[styles.micBtn, recording && styles.micBtnActive]}
          activeOpacity={0.85}
        >
          <Ionicons name={recording ? "stop" : "mic"} size={20} color={recording ? colors.white : colors.brand} />
        </TouchableOpacity>
        <TouchableOpacity onPress={sendText} style={styles.sendBtn} activeOpacity={0.85} disabled={busy}>
          <Ionicons name="send" size={18} color={colors.white} />
        </TouchableOpacity>
      </View>
      {recording && <Text style={styles.recHint}>Recording… tap ■ to send</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { flex: 1 },
  langRow: { flexDirection: "row", gap: space(2) as number, padding: space(3), flexWrap: "wrap" },
  langChip: {
    paddingHorizontal: space(3.5),
    paddingVertical: space(1.5),
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  langChipActive: { backgroundColor: colors.brand, borderColor: colors.brand },
  langText: { fontSize: 13, fontWeight: "800", color: colors.textMute },
  langTextActive: { color: colors.white },
  thread: { flex: 1 },
  threadContent: { padding: space(4), gap: space(3) as number },
  intro: { alignItems: "center", paddingVertical: space(10), gap: space(3) as number },
  introText: { textAlign: "center", color: colors.textFaint, fontWeight: "600", maxWidth: 300, lineHeight: 20 },
  bubbleRow: { flexDirection: "row" },
  rowMe: { justifyContent: "flex-end" },
  rowAgent: { justifyContent: "flex-start" },
  bubble: { maxWidth: "82%", borderRadius: radius.lg, padding: space(3.5) },
  bubbleMe: { backgroundColor: colors.brand, borderBottomRightRadius: radius.sm },
  bubbleAgent: { backgroundColor: colors.surface, borderBottomLeftRadius: radius.sm, borderWidth: 1, borderColor: colors.border },
  bubbleText: { fontSize: 15, fontWeight: "600", color: colors.text, lineHeight: 21 },
  bubbleTextMe: { color: colors.white },
  caseBox: { marginTop: space(2.5), borderTopWidth: 1, borderTopColor: colors.border, paddingTop: space(2.5) },
  caseId: { fontSize: 12, fontWeight: "800", color: colors.textMute, letterSpacing: 0.3 },
  caseMeta: { flexDirection: "row", alignItems: "center", gap: space(2) as number, marginTop: space(1.5) },
  caseAuthority: { fontSize: 12, fontWeight: "700", color: colors.textFaint },
  statusBadge: { paddingHorizontal: space(2.5), paddingVertical: 2, borderRadius: radius.pill },
  statusText: { fontSize: 11, fontWeight: "800", textTransform: "capitalize" },
  composer: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: space(2) as number,
    padding: space(3),
    borderTopWidth: 1,
    borderTopColor: colors.border,
    backgroundColor: colors.surface,
  },
  composerInput: {
    flex: 1,
    maxHeight: 110,
    backgroundColor: colors.surfaceAlt,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.lg,
    paddingHorizontal: space(4),
    paddingVertical: space(3),
    fontSize: 15,
    color: colors.text,
  },
  micBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    borderWidth: 1.5,
    borderColor: colors.brand,
    alignItems: "center",
    justifyContent: "center",
  },
  micBtnActive: { backgroundColor: colors.red, borderColor: colors.red },
  sendBtn: { width: 44, height: 44, borderRadius: 22, backgroundColor: colors.brand, alignItems: "center", justifyContent: "center" },
  recHint: { textAlign: "center", color: colors.red, fontWeight: "700", fontSize: 12, paddingBottom: space(2) },
});
