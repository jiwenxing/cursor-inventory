import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        // 优先使用环境变量，否则根据环境判断
        target: process.env.VITE_BACKEND_URL || 
                (process.env.DOCKER_ENV === 'true' ? 'http://backend:8000' : 'http://localhost:8000'),
        changeOrigin: true
      }
    }
  }
})
