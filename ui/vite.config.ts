import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../dashboard',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks: (id: string) => {
          if (id.includes('node_modules/recharts') || id.includes('node_modules/d3') || id.includes('node_modules/victory'))
            return 'vendor-recharts'
          if (id.includes('node_modules/lucide-react'))
            return 'vendor-lucide'
          if (id.includes('node_modules/react-dom') || id.includes('node_modules/react/') || id.includes('node_modules/react-is') || id.includes('node_modules/scheduler'))
            return 'vendor-react'
          if (id.includes('node_modules/easymde') || id.includes('node_modules/react-simplemde-editor') || id.includes('node_modules/codemirror'))
            return 'vendor-easymde'
          if (id.includes('node_modules/react-markdown') || id.includes('node_modules/remark') || id.includes('node_modules/rehype') || id.includes('node_modules/micromark') || id.includes('node_modules/unified') || id.includes('node_modules/mdast') || id.includes('node_modules/hast'))
            return 'vendor-markdown'
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8888',
      '/health': 'http://127.0.0.1:8888',
      '/ping': 'http://127.0.0.1:8888',
    },
  },
})
