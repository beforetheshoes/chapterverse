import js from '@eslint/js';
import tsPlugin from '@typescript-eslint/eslint-plugin';
import tsParser from '@typescript-eslint/parser';
import eslintConfigPrettier from 'eslint-config-prettier';
import vue from 'eslint-plugin-vue';
import vueParser from 'vue-eslint-parser';

export default [
  {
    ignores: ['.nuxt', '.output', 'coverage', 'dist', 'node_modules'],
  },
  js.configs.recommended,
  {
    files: ['**/*.vue'],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: tsParser,
        ecmaVersion: 'latest',
        sourceType: 'module',
        extraFileExtensions: ['.vue'],
      },
    },
    plugins: {
      vue,
      '@typescript-eslint': tsPlugin,
    },
    rules: {
      ...vue.configs['flat/recommended'].rules,
      'vue/no-undef-components': ['error', { ignorePatterns: ['Nuxt.*'] }],
      '@typescript-eslint/consistent-type-imports': 'error',
    },
  },
  {
    files: ['**/*.ts'],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
      },
      globals: {
        console: 'readonly',
      },
    },
    plugins: {
      '@typescript-eslint': tsPlugin,
    },
    rules: {
      '@typescript-eslint/consistent-type-imports': 'error',
    },
  },
  {
    files: ['cypress/**/*.{js,ts}'],
    languageOptions: {
      globals: {
        Cypress: 'readonly',
        after: 'readonly',
        afterEach: 'readonly',
        before: 'readonly',
        beforeEach: 'readonly',
        cy: 'readonly',
        describe: 'readonly',
        it: 'readonly',
      },
    },
  },
  {
    files: ['scripts/**/*.{js,mjs}'],
    languageOptions: {
      globals: {
        console: 'readonly',
        fetch: 'readonly',
        process: 'readonly',
        setTimeout: 'readonly',
      },
    },
  },
  {
    files: ['nuxt.config.ts'],
    languageOptions: {
      globals: {
        defineNuxtConfig: 'readonly',
        process: 'readonly',
      },
    },
  },
  {
    files: ['plugins/**/*.{js,ts}'],
    languageOptions: {
      globals: {
        defineNuxtPlugin: 'readonly',
        useRuntimeConfig: 'readonly',
      },
    },
  },
  {
    files: ['tests/**/*.{js,ts}'],
    languageOptions: {
      globals: {
        HTMLInputElement: 'readonly',
      },
    },
  },
  eslintConfigPrettier,
];
