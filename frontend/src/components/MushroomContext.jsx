import React, { createContext, useReducer, useEffect } from 'react';
import PropTypes from 'prop-types';
import { fetchMushrooms } from './api.js';

const MushroomContext = createContext();
// Initial state
const initialState = {
  mushrooms: [],
  loading: false,
  error: null,
  selectedMushroomId: null,
  searchTerm: '', // Initial search term
  currentPage: 1, // Initial page
  totalPages: 1 // Initial total pages
};

// Reducer to manage the state
const reducer = (state, action) => {
  switch (action.type) {
    case 'SET_SEARCH_RESULTS':
      return { 
        ...state, 
        mushrooms: action.payload.results, 
        totalPages: action.payload.totalPages, 
        loading: false 
      };
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };
    case 'SET_CURRENT_PAGE':
      return { ...state, currentPage: action.payload };
    case 'SET_SEARCH_TERM':
      return { ...state, searchTerm: action.payload };
    case 'SELECT_MUSHROOM':
      return { ...state, selectedMushroomId: action.payload };
    case 'CLEAR_SELECTION':
      return { ...state, selectedMushroomId: null };
    default:
      return state;
  }
};

// Define the Provider component
const MushroomProvider = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, initialState);

  useEffect(() => {
    const fetchData = async () => {
      dispatch({ type: 'SET_LOADING', payload: true }); 
      try {
        const data = await fetchMushrooms(state.searchTerm, state.currentPage); 
        dispatch({ type: 'SET_SEARCH_RESULTS', payload: data }); 
      } catch (error) {
        dispatch({ type: 'SET_ERROR', payload: error.message }); 
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false }); 
      }
    };

    fetchData(); 
  }, [state.searchTerm, state.currentPage]); 

  return (
    <MushroomContext.Provider value={{
      ...state,
      // Update context functions to directly dispatch actions
      fetchMushroomsData: (searchTerm, pageNumber) => {
        dispatch({ type: 'SET_SEARCH_TERM', payload: searchTerm });
        dispatch({ type: 'SET_CURRENT_PAGE', payload: pageNumber });
      },
      selectMushroom: (mushroomId) => dispatch({ type: 'SELECT_MUSHROOM', payload: mushroomId }),
      clearSelection: () => dispatch({ type: 'CLEAR_SELECTION' }) 
    }}>
      {children}
    </MushroomContext.Provider>
  );
};

// Add propTypes to MushroomProvider
MushroomProvider.propTypes = {
  children: PropTypes.node.isRequired
};

export { MushroomContext };
export default MushroomProvider;
