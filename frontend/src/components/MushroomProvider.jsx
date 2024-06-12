// MushroomProvider.jsx
import React, { createContext, useEffect, useReducer } from 'react';
import { fetchMushrooms } from '../api.js';

// ... (Other imports)

const MushroomContext = createContext(); 

// ... (Initial state and reducer logic) 

const MushroomProvider = ({ children }) => { 
  const [state, dispatch] = useReducer(reducer, initialState); 

  // Use the provided edit inside useEffect:
  useEffect(() => {
    const fetchData = async () => {
      dispatch({ type: 'SET_LOADING', payload: true }); 
      try {
        const data = await fetchMushrooms(); // Assuming no searchTerm or currentPage 
        dispatch({ type: 'SET_MUSHROOMS', payload: data });
      } catch (error) {
        dispatch({ type: 'SET_ERROR', payload: error.message });
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false }); 
      }
    };

    fetchData(); 
  }, []); 

  // ... (Other functions) 

  return (
    <MushroomContext.Provider value={{ state, dispatch, /* ...other functions */ }}>
      {children} 
    </MushroomContext.Provider>
  ); 
}; 

export default MushroomProvider;