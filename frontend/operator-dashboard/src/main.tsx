// Operator dashboard entry. Connects the WebSocket live feed and mounts the map. Skeleton.
import { connectLiveFeed } from "./lib/ws";

function App() {
  // TODO: render <RiskHeatmap/>, <CascadeChain/>, <StationDrilldown/>; subscribe to deltas.
  connectLiveFeed((delta) => void delta);
  return null;
}

export default App;
