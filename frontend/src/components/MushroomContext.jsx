// MushroomContext.jsx
// Import React, createContext, useReducer, and useState.
import React, { createContext, useReducer, useState } from 'react';
// Import the fetchMushrooms function from the api.js file.
import { fetchMushrooms } from './api.js';

// Create a new context using createContext. This will be used to share data across components.
const MushroomContext = createContext({
  // Define the initial values for the context. 
  // These can be anything (objects, arrays, functions, etc.), but here are some common ones:
  mushrooms: [], // An array to store the fetched mushrooms data
  loading: false, // A boolean to indicate if a request is in progress
  error: null, // An object to store any errors
  fetchMushroomsData: () => {}, // A function to fetch the mushrooms data
  dispatch: () => {} // The dispatch function from useReducer
});

// Define the initial state for the context. 
const initialState = {
  // An array to store the fetched mushrooms data.
  mushrooms: [],
  // A boolean to track whether data is being loaded.
  loading: false,
  // A string to store any error messages encountered during data fetching.
  error: null,
  // The current page number for pagination.
  currentPage: 1,
  // The total number of pages available for the current search.
  totalPages: null, 
  // The current search term entered by the user.
  searchTerm: '',
};

// Define the reducer function that will update the state based on the dispatched actions.
const reducer = (state, action) => {
  // Use a switch statement to handle different action types.
  switch (action.type) {
    // When the action type is 'SET_SEARCH_RESULTS', update the state with the new mushrooms data, total pages, and set loading to false.
    case 'SET_SEARCH_RESULTS':
      return { ...state, mushrooms: action.payload.results, totalPages: action.payload.totalPages, loading: false };
    // When the action type is 'SET_LOADING', update the loading state.
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    // When the action type is 'SET_ERROR', update the error state and set loading to false.
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };
    // When the action type is 'SET_CURRENT_PAGE', update the current page number.
    case 'SET_CURRENT_PAGE':
      return { ...state, currentPage: action.payload };
    // When the action type is 'SET_SEARCH_TERM', update the search term.
    case 'SET_SEARCH_TERM':
      return { ...state, searchTerm: action.payload };
    // If the action type doesn't match any case, return the current state.
    default:
      return state;
  }
};

// Define an asynchronous function to fetch mushrooms data from the API.
const fetchMushroomsData = async (searchTerm = '', pageNumber = 1) => {
  // Dispatch an action to set loading to true, indicating the start of data fetching.
  dispatch({ type: 'SET_LOADING', payload: true });
  // Clear any previous errors.
  dispatch({ type: 'SET_ERROR', payload: null });
  // Set the current page number.
  dispatch({ type: 'SET_CURRENT_PAGE', payload: pageNumber });
  // Set the search term.
  dispatch({ type: 'SET_SEARCH_TERM', payload: searchTerm });

  // Use a try-catch block to handle errors during the API request.
  try {
    // Call the fetchMushrooms function from the API with the search term and page number.
    const data = await fetchMushrooms(searchTerm, pageNumber);
    // Dispatch an action to update the search results with the fetched data.
    dispatch({ type: 'SET_SEARCH_RESULTS', payload: data });
  } catch (error) {
    // If an error occurs, dispatch an action to set the error message.
    dispatch({ type: 'SET_ERROR', payload: error.message });
  }
};


// Define the MushroomProvider component that will provide the context to its children.
const MushroomProvider = ({ children }) => {
  // Use the useReducer hook to manage the state and dispatch function.
  const [state, dispatch] = useReducer(reducer, initialState);

  // Render the MushroomContext.Provider component, making the state, fetchMushroomsData, and dispatch available to its children.
  return (
    <MushroomContext.Provider value={{ ...state, fetchMushroomsData, dispatch }}>
      {children}
    </MushroomContext.Provider>
  );
};

// Export the MushroomContext and MushroomProvider as named exports.
export { MushroomContext };
export default MushroomProvider;

