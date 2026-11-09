import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// In development, /api calls go to the FastAPI server (python -m server).
export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } },
})
