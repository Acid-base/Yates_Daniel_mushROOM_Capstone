module.exports = {
  preset: "ts-jest",
  testEnvironment: "node", // for Node.js environments
  testMatch: [
    "**/__tests__/**/*.+(ts|tsx|js)",
    "**/?(*.)+(spec|test).+(ts|tsx|js)",
  ], // configure files to test
  transform: {
    "^.+\\.(ts|tsx)$": "ts-jest", // Use ts-jest to transform TypeScript files
  },
};
