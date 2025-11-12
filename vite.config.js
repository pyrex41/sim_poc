import { defineConfig } from 'vite'
import { plugin } from 'vite-plugin-elm'

export default defineConfig({
  plugins: [plugin()],
  server: {
    port: 5173
  }
})