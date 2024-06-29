module.exports = {
extends: ['eslint:recommended', 'plugin:react/recommended'],
  parser: '@babel/eslint-parser',
parserOptions: {
 ecmaVersion: 2020,
 sourceType: 'module',
 ecmaFeatures: {
   jsx: true,
 },
},
  plugins: ['react', 'node'], // Add 'node' to the plugins array
  rules: {
    'react/prop-types': 'off',
  },
};
