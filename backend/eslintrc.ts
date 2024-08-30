module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  parserOptions: {
    project: './tsconfig.json',
    sourceType: 'module'
  },
  plugins: [
    '@typescript-eslint',
    'jest'
  ],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:jest/recommended'
  ],
  rules: {
    'no-console': 'warn',
    'no-unused-vars': 'warn',
    'indent': ['warn', 2],
    'linebreak-style': ['warn', 'unix']
  },
  env: {
    node: true,
    jest: true
  }
};
