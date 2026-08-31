import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'CarTech Werkstatt',
        short_name: 'CarTech',
        description: 'Werkstattanwendung für die Fahrzeug- und Reifenservice-Erfassung.',
        lang: 'de',
        start_url: '/',
        scope: '/',
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
        navigateFallback: '/index.html',
      },
    }),
  ],
})
