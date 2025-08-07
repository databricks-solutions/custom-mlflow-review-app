import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: [
          [
            'babel-plugin-formatjs',
            {
              idInterpolationPattern: '[sha512:contenthash:base64:6]',
              ast: true
            }
          ]
        ]
      }
    })
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  optimizeDeps: {
    include: ['@databricks/design-system', 'react-intl', 'json-bigint', 'lodash', 'cookie', 'qs', 'hoist-non-react-statics', '@emotion/react', '@emotion/cache']
  },
  define: {
    global: 'globalThis',
    'process.env': {},
    'process.env.NODE_ENV': JSON.stringify('production'),
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
    // Enable history API fallback for React Router
    historyApiFallback: true,
  },
  build: {
    outDir: 'build',
  }
})