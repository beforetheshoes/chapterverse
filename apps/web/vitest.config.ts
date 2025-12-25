import vue from '@vitejs/plugin-vue';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    include: ['tests/unit/**/*.test.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      include: ['app/**/*.{ts,vue}', 'components/**/*.{ts,vue}', 'utils/**/*.{ts,vue}'],
      exclude: ['**/*.d.ts', 'cypress/**', 'tests/**', 'node_modules/**'],
      lines: 95,
      statements: 95,
      functions: 95,
      branches: 95,
    },
  },
});
