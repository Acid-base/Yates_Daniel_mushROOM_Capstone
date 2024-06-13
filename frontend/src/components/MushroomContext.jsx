// src/components/MushroomContext.jsx
import React, { createContext, useContext, useEffect, useReducer } from 'react';
import { fetchMushroomDetails } from '../api';
import { API_BASE_URL } from './constants'; // Import API_BASE_URL
import PropTypes from 'prop-types'; // Import PropTypes

const MushroomContext = createContext();

const initialState = {
  mushrooms: [],
  loading: true, 
  error: null,
  selectedMushroom: null,
  selectedMushroomId: null, // Added selectedMushroomId to state
  isAuthenticated: false,
  setIsAuthenticated: () => {},
  searchTerm: '', // Default to an empty string
  currentPage: 1, // Default to page 1
};

const reducer = (state, action) => {
  switch (action.type) {
    // ... other cases ...
    case 'SELECT_MUSHROOM': // Add the SELECT_MUSHROOM case
      return { ...state, selectedMushroomId: action.payload }; 
    default:
      return state;
  }
};

export const useMushroomContext = () => {
  return useContext(MushroomContext);
};

export const MushroomProvider = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, initialState);
  const { searchTerm, currentPage } = state; // Destructure here
  useEffect(() => {
    // ... (fetchMushrooms logic remains the same) ...
  }, [searchTerm, currentPage]);

  const handleMushroomSelect = (mushroomId) => {
    dispatch({ type: 'SELECT_MUSHROOM', payload: mushroomId }); // Dispatch SELECT_MUSHROOM
    fetchMushroomDetails(mushroomId)
      .then(details => dispatch({ type: 'FETCH_MUSHROOM_DETAILS_SUCCESS', payload: details }))
      .catch(error => dispatch({ type: 'FETCH_MUSHROOM_DETAILS_ERROR', payload: error.message }));
  };

  return (
    <MushroomContext.Provider value={{ state, dispatch, selectMushroom: handleMushroomSelect }}> 
      {children} 
    </MushroomContext.Provider>
  );
};

MushroomProvider.propTypes = {
  children: PropTypes.node.isRequired,
};