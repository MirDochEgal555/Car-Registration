import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

const basePath = process.env.VITE_BASE_PATH || '/'

export default defineConfig({
  base: basePath,
  server: {
    // The frontend can call the versioned API with the same relative URL in
    // development and production. In production, the reverse proxy forwards
    // `/api` to FastAPI.
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'CarTech Werkstatt',
        short_name: 'CarTech',
        description: 'Werkstattanwendung für die Fahrzeug- und Reifenservice-Erfassung.',
        lang: 'de',
        start_url: basePath,
        scope: basePath,
        display: 'standalone',
        theme_color: '#17241f',
        background_color: '#f4f7f4',
      },
      pwaAssets: {
        image: 'public/pwa-icon.svg',
        injectThemeColor: false,
      },
      workbox: {
        cleanupOutdatedCaches: true,
        clientsClaim: true,
        globPatterns: ['**/*.{js,css,html,png,ico,svg,webmanifest}'],
        skipWaiting: true,
        navigateFallback: `${basePath}index.html`,
      },
    }),
  ],
})
