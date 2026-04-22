import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react()],
    server: {
      host: '0.0.0.0',
      proxy: {
        '/api/inventory': {
          target:
            env.VITE_INVENTORY_PROXY_TARGET ?? 'http://127.0.0.1:8000',
          changeOrigin: true,
        },
        '/api/catalog': {
          target: env.VITE_CATALOG_PROXY_TARGET ?? 'http://127.0.0.1:8001',
          changeOrigin: true,
        },
      },
    },
  }
})
