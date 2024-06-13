import React, { createContext, useEffect, useReducer } from 'react';
import PropTypes from 'prop-types';
import { fetchMushrooms } from '../api.js';

// Create the context object
const MushroomContext = createContext();

// Define the initial state
const initialState = {
  mushrooms: [], // Array to hold fetched mushrooms
  isLoading: false, // Flag to indicate if data is being fetched
  selectedMushroomId: null, // ID of the currently selected mushroom
  isAuthenticated: false, // Flag for authentication status
};

// Define the reducer function
const reducer = (state, action) => {
  switch (action.type) {
    case 'SET_MUSHROOMS':
      return { ...state, mushrooms: action.payload, isLoading: false };
    case 'SET_LOADING':
      return { ...state, isLoading: true };
    case 'SET_SELECTED_MUSHROOM':
      return { ...state, selectedMushroomId: action.payload };
    case 'CLEAR_SELECTION':
      return { ...state, selectedMushroomId: null };
    case 'SET_AUTHENTICATED':
      return { ...state, isAuthenticated: action.payload };
    default:
      return state;
  }
};

// The Provider component
const MushroomProvider = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, initialState);

  const fetchMushroomsData = async () => {
    dispatch({ type: 'SET_LOADING' });
    try {
      const mushrooms = await fetchMushrooms();
      dispatch({ type: 'SET_MUSHROOMS', payload: mushrooms });
    } catch (error) {
      console.error('Error fetching mushrooms:', error);
    }
  };

  useEffect(() => {
    fetchMushroomsData();
  }, []); 

  const clearSelection = () => {
    dispatch({ type: 'CLEAR_SELECTION' });
  };

  const setSelectedMushroom = (mushroomId) => {
    dispatch({ type: 'SET_SELECTED_MUSHROOM', payload: mushroomId });
  };

  // Add setAuthenticated function for handling authentication
  const setAuthenticated = (isAuthenticated) => {
    dispatch({ type: 'SET_AUTHENTICATED', payload: isAuthenticated });
  };

  const value = {
    mushrooms: state.mushrooms,
    isLoading: state.isLoading,
    selectedMushroomId: state.selectedMushroomId,
    isAuthenticated: state.isAuthenticated, // Make isAuthenticated accessible
    fetchMushroomsData, // Pass fetchMushroomsData to context
    clearSelection,
    setSelectedMushroom, 
    setAuthenticated // Make setAuthenticated accessible
  };

  return (
    <MushroomContext.Provider value={value}>
      {children}
    </MushroomContext.Provider>
  );
};

MushroomProvider.propTypes = {
  children: PropTypes.node.isRequired, // Add prop type validation for children
};

export { MushroomProvider, MushroomContext };
