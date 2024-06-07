// .eslintrc.cjs 
// This file is likely located in the root of your project folder.
// There should be some kind of package manager config file on the same level
// This is a configuration file for ESLint, a popular JavaScript linter that helps you write cleaner and more consistent code.
module.exports = {
  //  The root property indicates that this is the base ESLint configuration file for your project. Any other configuration files will inherit from this one.
  root: true,
  // The env property defines the environments your code will run in. 
  // 'browser: true' tells ESLint that your code will run in a browser environment, so it will enable rules specific to browser globals like 'window' and 'document'.
  // 'es2020: true' tells ESLint to use the ES2020 version of JavaScript (also known as ECMAScript 2020), so you can use modern JavaScript features.
  env: { browser: true, es2020: true },
  // The extends property allows you to extend your ESLint configuration from other configurations. In this case, you're extending:
  // - 'eslint:recommended': The recommended set of rules provided by ESLint. This is a good starting point for any project.
  // - 'plugin:react/recommended': The recommended set of rules for React projects provided by the eslint-plugin-react plugin. This ensures you're following React best practices.
  // - 'plugin:react/jsx-runtime': This plugin removes the requirement to import React in every file that uses JSX, making your code cleaner.
  // - 'plugin:react-hooks/recommended': The recommended set of rules for React Hooks provided by the eslint-plugin-react-hooks plugin. This helps prevent common mistakes when using hooks.
  extends: [
    'eslint:recommended',
    'plugin:react/recommended',
    'plugin:react/jsx-runtime',
    'plugin:react-hooks/recommended',
  ],
  // The ignorePatterns property tells ESLint to ignore specific files or folders when linting. 
  // Here, it's ignoring the 'dist' folder (usually the output of your build process) and the '.eslintrc.cjs' file itself.
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  // The parserOptions property tells ESLint how to parse your code. 
  // 'ecmaVersion: 'latest'' tells it to use the latest supported ECMAScript version. 
  // 'sourceType: 'module'' tells it that your code is written in ES Modules format (using 'import' and 'export' statements).
  parserOptions: { ecmaVersion: 'latest', sourceType: 'module' },
  // The settings property allows you to configure specific rules or plugins with project-specific options. 
  // Here, you're telling the 'react' plugin to use version '18.2' of React.
  settings: { react: { version: '18.2' } },
  // The plugins property lists additional ESLint plugins you want to use. 
  // In this case, you're using the 'react-refresh' plugin, which helps with faster development by only refreshing components that have actually changed.
  plugins: ['react-refresh'],
  // The rules property allows you to override or extend the rules from the configurations you've extended.
  rules: {
    // 'react/jsx-no-target-blank': 'off' disables the rule that enforces 'target="_blank"' links to have a 'rel="noopener noreferrer"' attribute for security reasons.
    'react/jsx-no-target-blank': 'off',
    // 'react-refresh/only-export-components': ['warn', { allowConstantExport: true }] configures the 'react-refresh' plugin to only allow exporting React components from files, 
    // but it also allows exporting constant values (e.g., strings or numbers) with a warning.
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
  },
}
