// gimnasioReact/vite.config.ts

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  
  // Path aliases matching tsconfig.json
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@api': path.resolve(__dirname, './src/api'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@types': path.resolve(__dirname, './src/types'),
      '@schemas': path.resolve(__dirname, './src/schemas'),
      '@assets': path.resolve(__dirname, './src/assets'),
    },
  },
  
  // Dev server config
  server: {
    port: 5173,
    strictPort: true,
    host: true, // allow external access
    
    // Proxy API calls to Django
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        // Rewrite: remove /api prefix if Django expects it at root
        // rewrite: (path) => path.replace(/^\/api/, ''),
        
        // Configure headers for cookies
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            // Forward cookies from browser to Django
            const cookie = req.headers.cookie;
            if (cookie) {
              proxyReq.setHeader('Cookie', cookie);
            }
            
            // Forward CSRF token
            const csrfToken = req.headers['x-csrftoken'];
            if (csrfToken) {
              proxyReq.setHeader('X-CSRFToken', csrfToken);
            }
            
            // Forward Gym ID for multi-tenant
            const gymId = req.headers['x-gym-id'];
            if (gymId) {
              proxyReq.setHeader('X-Gym-ID', gymId);
            }
          });
          
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            // Forward Set-Cookie headers from Django to browser
            const setCookie = proxyRes.headers['set-cookie'];
            if (setCookie) {
              // Vite dev server doesn't automatically forward cookies
              // This ensures HttpOnly cookies work in dev
            }
          });
        },
      },
    },
  },
  
  // Build config for production
  build: {
    // Output to Django staticfiles directory
    outDir: '../gimnasioApp/static',
    emptyOutDir: true,
    
    // Generate manifest for Django to reference
    manifest: true,
    
    // Sourcemaps for debugging
    sourcemap: true,
    
    // Chunk splitting for caching
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          query: ['@tanstack/react-query'],
          forms: ['react-hook-form', '@hookform/resolvers', 'zod'],
          ui: ['lucide-react', 'clsx', 'tailwind-merge'],
        },
        // Stable chunk names for caching
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.');
          const ext = info[info.length - 1];
          if (/\.(png|jpe?g|gif|svg|webp|avif)$/.test(assetInfo.name)) {
            return `assets/images/[name]-[hash].${ext}`;
          }
          if (/\.(woff2?|ttf|eot)$/.test(assetInfo.name)) {
            return `assets/fonts/[name]-[hash].${ext}`;
          }
          return `assets/[ext]/[name]-[hash].${ext}`;
        },
      },
    },
    
    // Minification
    minify: 'esbuild',
    target: 'es2020',
    
    // CSS code splitting
    cssCodeSplit: true,
    
    // Report compressed sizes
    reportCompressedSize: true,
  },
  
  // CSS config
  css: {
    modules: {
      localsConvention: 'camelCaseOnly',
      generateScopedName: '[name]__[local]___[hash:base64:5]',
    },
    preprocessorOptions: {
      scss: {
        api: 'modern-compiler',
      },
    },
  },
  
  // Define global constants
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
    __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
  },
  
  // Optimize deps
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@tanstack/react-query',
      'react-hook-form',
      '@hookform/resolvers/zod',
      'zod',
      'axios',
      'clsx',
      'tailwind-merge',
      'lucide-react',
    ],
  },
});