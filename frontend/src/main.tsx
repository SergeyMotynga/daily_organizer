import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./app/app";
import "./styles.css";
import "./redesign.css";

try {
  const savedTheme = localStorage.getItem("daily-organizer-theme");
  document.documentElement.dataset.theme = savedTheme === "dark" ? "dark" : "light";
} catch {
  document.documentElement.dataset.theme = "light";
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
