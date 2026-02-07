import vue from '@vitejs/plugin-vue';
import { URL, fileURLToPath } from 'node:url';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '#imports': fileURLToPath(new URL('./tests/nuxt-imports.ts', import.meta.url)),
      '~': fileURLToPath(new URL('./app', import.meta.url)),
    },
  },
  test: {
    environment: 'jsdom',
    include: ['tests/unit/**/*.test.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      include: ['app/**/*.{ts,vue}', 'components/**/*.{ts,vue}', 'utils/**/*.{ts,vue}'],
      exclude: ['**/*.d.ts', 'cypress/**', 'tests/**', 'node_modules/**'],
      thresholds: {
        lines: 95,
        statements: 95,
        functions: 95,
        branches: 95,
        perFile: true,
      },
    },
  },
});
