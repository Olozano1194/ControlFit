import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss()
  ],
  server: {
    watch: {
      // Ignore the corrupted leftover folder until it can be deleted (chkdsk /f).
      ignored: ['**/node_modules_corrupto/**'],
    },
  },
})
