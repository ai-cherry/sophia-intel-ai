import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 3000
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@headlessui/react': path.resolve(__dirname, './node_modules/@headlessui/react'),
      '@heroicons/react': path.resolve(__dirname, './node_modules/@heroicons/react')
    }
  }
})