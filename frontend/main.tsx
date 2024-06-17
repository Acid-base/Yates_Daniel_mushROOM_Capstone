// src/main.jsx
import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { MushroomProvider } from "./components/MushroomContext";

const root = createRoot(document.getElementById("root"));

root.render(
// src/main.jsx
import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { MushroomProvider } from "./components/MushroomContext";

// Ensure the root element exists
const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element not found");
}

const root = createRoot(rootElement);

root.render(
  <React.StrictMode>
    <MushroomProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </MushroomProvider>
  </React.StrictMode>
);
    <MushroomProvider>
      <BrowserRouter>
        <App />
      </Browser
