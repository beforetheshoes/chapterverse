<template>
  <div class="min-h-screen bg-slate-950/5 text-slate-900">
    <section class="mx-auto flex w-full max-w-4xl flex-col gap-6 px-6 py-12">
      <Card class="shadow-lg" data-test="welcome-card">
        <template #title>
          <div class="flex items-center gap-3 text-2xl font-semibold">
            <i class="pi pi-book text-emerald-600" aria-hidden="true"></i>
            <span data-test="hero-title">The Seedbed</span>
          </div>
        </template>
        <template #subtitle>
          <span class="text-base text-slate-600" data-test="hero-subtitle">
            Build a reading history, capture insights, and keep every edition within reach.
          </span>
        </template>
        <template #content>
          <div class="flex flex-col gap-4">
            <p class="text-sm text-slate-600">
              PrimeVue v4 and the Aura theme are live. Tailwind utilities handle layout tweaks while
              PrimeVue powers the core UI components.
            </p>
            <div class="flex flex-col gap-2">
              <label class="text-sm font-medium text-slate-700" for="email">Stay in the loop</label>
              <InputText
                id="email"
                v-model="email"
                class="w-full"
                placeholder="you@theseedbed.app"
                data-test="hero-email-input"
              />
            </div>
          </div>
        </template>
        <template #footer>
          <div class="flex flex-wrap items-center gap-3">
            <NuxtLink
              to="/library"
              class="inline-flex items-center gap-2 rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500"
              data-test="primary-cta"
            >
              <i class="pi pi-arrow-right" aria-hidden="true"></i>
              Explore library
            </NuxtLink>
            <NuxtLink
              to="/books/search"
              class="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              data-test="secondary-cta"
            >
              Add a book
            </NuxtLink>
          </div>
        </template>
      </Card>

      <Card class="border border-slate-200/60" data-test="status-card">
        <template #content>
          <div class="flex items-start gap-4">
            <div class="rounded-full bg-emerald-100 p-3 text-emerald-700">
              <i class="pi pi-check" aria-hidden="true"></i>
            </div>
            <div>
              <p class="text-sm font-semibold text-slate-900">Frontend foundation ready</p>
              <p class="text-sm text-slate-600">
                Nuxt 4.2.2, PrimeVue, and Supabase client wiring are in place for the next build
                phase.
              </p>
            </div>
          </div>
        </template>
      </Card>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import Card from 'primevue/card';
import InputText from 'primevue/inputtext';

const email = ref('');
</script>
