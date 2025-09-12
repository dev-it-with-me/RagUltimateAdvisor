import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import { SWRProvider } from "./providers/SWRProvider.tsx";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <SWRProvider>
      <App />
    </SWRProvider>
  </StrictMode>
);
