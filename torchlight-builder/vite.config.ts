import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 3000,
    /** 3000 被占用时自动换端口，避免启动失败 */
    strictPort: false,
    /** 监听 0.0.0.0，本机 localhost / 局域网 / 部分环境才可访问 */
    host: true,
    open: false
  }
})
