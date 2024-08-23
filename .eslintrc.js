module.exports = {
  extends: ['eslint:recommended', 'plugin:react/recommended', '@nighttrax/eslint-config-tsx'], // Keep your base config
  parser: '@babel/eslint-parser',
  parserOptions: {
    project: "./tsconfig.json", // Crucial for type-aware linting
    tsconfigRootDir: __dirname, // Tells ESLint where your tsconfig.json is
    ecmaVersion: 2020,
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true,
    },
  },
  plugins: ['react'],
  rules: {
    // === Error Catching ===

    "no-console": "warn", // Warn about console logs (can be "error")
    "no-debugger": "error", // Prevent debugger statements in production
    "no-unused-vars": "error", // Catch unused variables
    "no-undef": "error", // Ensure all variables are defined
    "no-empty": "warn", // Warn about empty blocks (can be "error")
    "no-unreachable": "error", // Detect unreachable code
    "no-constant-condition": "error", // Find conditions that are always true/false
    "no-dupe-keys": "error", // Prevent duplicate keys in objects
    "no-extra-semi": "warn", // Avoid unnecessary semicolons
    "no-cond-assign": "error", // Disallow assignment in conditions
    "no-self-compare": "error", // Catch useless self-comparisons
    "no-use-before-define": "error", // Enforce variable definitions before use

    // === Type Checking (requires TypeScript) ===

    "@typescript-eslint/no-explicit-any": "warn", // Discourage using "any"
    "@typescript-eslint/no-unsafe-assignment": "warn", // Prevent unsafe assignments
    "@typescript-eslint/no-unsafe-member-access": "warn", // Flag unsafe property access
    "@typescript-eslint/no-unsafe-call": "warn", // Warn about unsafe function calls
    "@typescript-eslint/no-unsafe-return": "warn", // Catch unsafe return values
    "@typescript-eslint/restrict-template-expressions": "warn", // Limit types in template strings
    "@typescript-eslint/no-misused-promises": "warn", // Ensure promises are used correctly
    "@typescript-eslint/no-floating-promises": "warn", // Prevent unhandled promises
    "@typescript-eslint/explicit-module-boundary-types": "warn", // Encourage explicit return types
    "@typescript-eslint/no-unused-vars": "error", // TypeScript-specific unused variable check
    'react/prop-types': 'off',
  },
};
