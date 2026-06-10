// PNR registration + live status / re-route view. Skeleton.
import { RerouteCard } from "../components/RerouteCard";

export default function Home() {
  // TODO: register PNR, subscribe to push, render live status.
  return (
    <main>
      <h1>CascadeGuard</h1>
      <p>Register your PNR to get re-routed before the delay is announced.</p>
      <RerouteCard />
    </main>
  );
}
