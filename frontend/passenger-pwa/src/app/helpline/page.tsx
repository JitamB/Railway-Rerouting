// Helpline screen: chat with the support agent by text or regional-language speech. Skeleton.
import { HelplineChat } from "../../components/HelplineChat";

export default function HelplinePage() {
  return (
    <main>
      <h1>Helpline</h1>
      <p>Ask a question or raise a complaint — type or speak in your language.</p>
      <HelplineChat />
    </main>
  );
}
