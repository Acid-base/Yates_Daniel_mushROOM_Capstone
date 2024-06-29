// src/components/MushroomContext.jsx
import React, { createContext, useEffect, useReducer, useState } from 'react';
import { fetchMushroomDetails, fetchMushrooms } from '../api';
const MushroomContext = createContext();

// Initial state
const initialState = {
  mushrooms: [], // Initially empty
  loading: true, // Set loading to true initially
  error: null, // Initialize error to null
  selectedMushroomId: null,
  selectedMushroom: null, // Add this line
};

const reducer = (state, action) => {
  switch (action.type) {
    case 'SET_MUSHROOMS':
      return { ...state, mushrooms: action.payload, loading: false };
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };
    case 'SELECT_MUSHROOM':
      return { ...state, selectedMushroomId: action.payload, loading: true }; // Set loading to true before fetching details
    case 'SET_SELECTED_MUSHROOM': // New action for fetching details
      return { ...state, selectedMushroom: action.payload, loading: false };
    case 'CLEAR_SELECTION':
      return { ...state, selectedMushroomId: null, selectedMushroom: null };
    default:
      return state;
  }
};

const MushroomProvider = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, initialState);
  const [searchTerm, setSearchTerm] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    const fetchData = async () => {
      // dispatch({ type: 'SET_LOADING', payload: true }); // Already handled in initial state
      try {
        const data = await fetchMushrooms(searchTerm, currentPage);
        dispatch({ type: 'SET_MUSHROOMS', payload: data });
      } catch (error) {
        dispatch({ type: 'SET_ERROR', payload: error.message });
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    };

    fetchData(); // Fetch data initially
  }, [searchTerm, currentPage]);

  // Fetch details when selectedMushroomId changes
  useEffect(() => {
    if (state.selectedMushroomId) {
      const fetchDetails = async () => {
        try {
          const data = await fetchMushroomDetails(state.selectedMushroomId);
          dispatch({ type: 'SET_SELECTED_MUSHROOM', payload: data });
        } catch (error) {
          dispatch({ type: 'SET_ERROR', payload: error.message });
        }
      };
      fetchDetails();
    }
  }, [state.selectedMushroomId]);

  return (
    <MushroomContext.Provider
      value={{
        ...state,
        setSearchTerm,
        setCurrentPage, // Provide setCurrentPage
        selectMushroom: mushroomId =>
          dispatch({ type: 'SELECT_MUSHROOM', payload: mushroomId }),
        clearSelection: () => dispatch({ type: 'CLEAR_SELECTION' }),
        fetchMushrooms, // Add fetchMushrooms to the value
      }}
    >
      {children}
    </MushroomContext.Provider>
  );
};

export { MushroomContext };
export default MushroomProvider;
