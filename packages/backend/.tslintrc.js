module.exports = {
  "extends": "eslint:recommended",
  "rules": {
    "no-console": "error", // Disallow console.log, prefer dedicated logging
    "no-unused-vars": "error", // Catch unused variables, potential bugs
    "indent": ["warn", 2], 
    "linebreak-style": ["warn", "unix"], 
    "quotes": ["warn", "double"], 
    "semi": ["warn", "always"],
    // Add more rules for better error catching:
    "no-undef": "error", // Disallow using undefined variables
    "no-unreachable": "error", // Catch unreachable code after return, throw etc.
    "eqeqeq": "error", // Require === and !==, avoid type coercion bugs
    "no-empty": "error", // Disallow empty blocks, potential logic errors
    "curly": "error", // Enforce consistent brace style for control flow
  }
};

  
