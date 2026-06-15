import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
// Offline, bundled display + mono fonts (Latin only — Arabic stays Plex).
import "@fontsource-variable/archivo/wght.css";
import "@fontsource-variable/archivo/wdth.css";
import "@fontsource/share-tech-mono/400.css";
import "@fontsource-variable/jetbrains-mono/wght.css";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
