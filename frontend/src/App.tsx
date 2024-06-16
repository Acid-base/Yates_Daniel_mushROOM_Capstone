// frontend/src/App.tsx
import React, { useState, createContext } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import MushroomSearch from "./components/MushroomSearch";
import MushroomDetails from "./components/MushroomDetails"; // Assuming you have this component
import BlogPage from "./components/BlogPage";
import "./App.css";

interface Mushroom {
  id: number;
  // ... other properties
}

export const MushroomContext = createContext<{
  selectedMushroom: Mushroom | null;
  selectMushroom: (mushroom: Mushroom) => void;
}>({
  selectedMushroom: null,
  selectMushroom: () => {},
});

const queryClient = new QueryClient();

function App() {
  const [selectedMushroom, setSelectedMushroom] = useState<Mushroom | null>(
    null,
  );

  const handleMushroomSelect = (mushroom: Mushroom) => {
    setSelectedMushroom(mushroom);
  };

  return (
    <QueryClientProvider client={queryClient}>
      <MushroomContext.Provider
        value={{ selectedMushroom, selectMushroom: handleMushroomSelect }}
      >
        <Router>
          <div className="App">
            <Routes>
              <Route path="/" element={<MushroomSearch />} />
              <Route path="/mushroom/:id" element={<MushroomDetails />} />
              <Route path="/blog" element={<BlogPage />} />
            </Routes>
          </div>
        </Router>
      </MushroomContext.Provider>
    </QueryClientProvider>
  );
}

export default App;
