import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({
  plugins: [react()],
  // Specify the entry point for your application
  root: '', // If your main component is in the 'src' directory
  build: {
    outDir: '../dist', // Adjust if needed
    sourcemap: true, // Generate source maps
    minify: true, // Minify code
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'], // Vendor chunk for better caching
        },
      },
    },
  },
  optimizeDeps: {
    include: ['react', 'react-dom'], // Pre-bundle these dependencies
  },
  server: {
    port: 3000,
  },
});
