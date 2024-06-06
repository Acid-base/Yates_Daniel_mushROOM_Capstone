// MushroomContext.jsx
import React, { createContext, useReducer, useState } from 'react';
import { fetchMushrooms } from './api.js';

const MushroomContext = createContext({
  mushrooms: [],
  loading: false,
  error: null,
  fetchMushroomsData: () => {},
  dispatch: () => {}
});

// Initial State (Example)
const initialState = {
  mushrooms: [],
  loading: false,
  error: null,
  currentPage: 1,
  searchTerm: '',
  totalPages: null, 
  searchTerm: '',
  fetchMushroomsData: () => {},
  dispatch: () => {}
});

const initialState = {
  mushrooms: [],
  loading: false,
  error: null,
  currentPage: 1,
  totalPages: null, 
  searchTerm: '',
};

// Reducer Function (Example - You'll need to customize this)
const reducer = (state, action) => {
  switch (action.type) {
    case 'SET_SEARCH_RESULTS':
      return { ...state, mushrooms: action.payload.results, totalPages: action.payload.totalPages, loading: false };
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };
    case 'SET_CURRENT_PAGE':
      return { ...state, currentPage: action.payload };
    case 'SET_SEARCH_TERM':
      return { ...state, searchTerm: action.payload };
    default:
      return state;
  }
};

// Fetch Mushrooms Data Function (Modified to include Total Pages)
const fetchMushroomsData = async (searchTerm = '', pageNumber = 1) => {
  dispatch({ type: 'SET_LOADING', payload: true });
  dispatch({ type: 'SET_ERROR', payload: null });
  dispatch({ type: 'SET_CURRENT_PAGE', payload: pageNumber });
  dispatch({ type: 'SET_SEARCH_TERM', payload: searchTerm });

  try {
    const data = await fetchMushrooms(searchTerm, pageNumber);
    dispatch({ type: 'SET_SEARCH_RESULTS', payload: data });
  } catch (error) {
    dispatch({ type: 'SET_ERROR', payload: error.message });
  }
};


const MushroomProvider = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, initialState);

  return (
    <MushroomContext.Provider value={{ ...state, fetchMushroomsData, dispatch }}>
      {children}
    </MushroomContext.Provider>
  );
};

export { MushroomContext };
export default MushroomProvider;
