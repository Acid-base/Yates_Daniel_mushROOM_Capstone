// src/main.jsx
import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { MushroomProvider } from "./components/MushroomContext";

const root = createRoot(document.getElementById("root"));

root.render(
  <React.StrictMode>
    <MushroomProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </MushroomProvider>
  </React.StrictMode>,
);
