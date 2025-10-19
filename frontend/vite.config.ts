import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const API_BASE = process.env.VITE_API_BASE || 'http://localhost:8080'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // If API base is absolute, the frontend will call it directly; this proxy helps when base is empty
      '/upload': API_BASE,
      '/run': API_BASE,
      '/status': API_BASE,
      '/logs': API_BASE,
      '/results': API_BASE,
      '/download': API_BASE,
      '/jobs': API_BASE,
    }
  },
  build: {
    outDir: 'dist'
  }
})
