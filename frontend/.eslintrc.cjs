module.exports = {
  root: true,
  env: {
    browser: true, // Enable browser globals
    es2020: true, // Enable ES2020 features
    node: true, // Enable Node.js globals (if applicable to your setup)
  },
  parser: "@typescript-eslint/parser",
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
    project: ["./tsconfig.json"],
  },
  plugins: ["@typescript-eslint", "react-refresh", "import"], // Add 'import' plugin
  extends: [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended",
    "plugin:prettier/recommended", // Add this line for Prettier integration
    // Consider adding: 'plugin:jsx-a11y/recommended' for accessibility
  ],
  ignorePatterns: ["dist", ".eslintrc.cjs", "node_modules"], // Ignore common build folders
  rules: {
    "react-refresh/only-export-components": [
      "warn",
      { allowConstantExport: true },
    ],
    // Add rules for import order and optimization
    "import/order": [
      "error",
      {
        groups: [
          "builtin",
          "external",
          "internal",
          "parent",
          "sibling",
          "index",
        ],
        "newlines-between": "always",
        alphabetize: { order: "asc", caseInsensitive: true },
      },
    ],
    "import/no-extraneous-dependencies": [
      "error",
      { devDependencies: ["**/*.test.ts", "**/*.test.tsx", "vite.config.ts"] },
    ],
    // Other recommended rules:
    "no-console": "warn", // Warn about console logs in production
    "no-unused-vars": "off", // Let TypeScript handle unused vars
    "@typescript-eslint/no-unused-vars": "warn",
    "react/prop-types": "off", // Not needed with TypeScript
    // Enforce consistent indentation (choose spaces or tabs)
    indent: ["error", 2, { SwitchCase: 1 }],
    // Enforce consistent use of single or double quotes
    quotes: ["error", "single"],
    // Enforce semicolons
    semi: ["error", "always"],
  },
  settings: {
    react: {
      version: "detect", // Automatically detect React version
    },
  },
};
