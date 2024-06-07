// src/mushroomReducer.js 
// Define the initial state for the reducer. 
// It currently only holds the ID of the selected mushroom, which is initially set to null.
const initialState = {
  selectedMushroomId: null,
};

// Define the mushroomReducer function, which takes the current state and an action as arguments.
const mushroomReducer = (state, action) => {
  // Use a switch statement to handle different action types.
  switch (action.type) {
    // If the action type is 'SELECT_MUSHROOM'...
    case 'SELECT_MUSHROOM':
      // ...return a new state object where 'selectedMushroomId' is updated with the payload of the action.
      return { ...state, selectedMushroomId: action.payload };
    // If the action type is 'CLEAR_SELECTION'...
    case 'CLEAR_SELECTION': 
      // ...return a new state object where 'selectedMushroomId' is set back to null.
      return { ...state, selectedMushroomId: null };
    // If the action type doesn't match any of the cases...
    default:
      // ...return the current state without any modifications.
      return state;
  }
};

// Export the mushroomReducer as the default export.
export default mushroomReducer;
