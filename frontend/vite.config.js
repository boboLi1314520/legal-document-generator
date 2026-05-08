import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8002',
        changeOrigin: true,
        timeout: 300000  // 5分钟超时
      }
    }
  },
  // 添加编码配置
  build: {
    chunkSizeWarningLimit: 1500
  }
})
