// src/mushroomReducer.js 
const initialState = {
  selectedMushroomId: null,
};

const mushroomReducer = (state, action) => {
  switch (action.type) {
    case 'SELECT_MUSHROOM':
      return { ...state, selectedMushroomId: action.payload };
    case 'CLEAR_SELECTION': 
      return { ...state, selectedMushroomId: null };
    default:
      return state;
  }
};

export default mushroomReducer;

