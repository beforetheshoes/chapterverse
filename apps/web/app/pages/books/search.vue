<template>
  <div class="min-h-screen bg-slate-950/5 text-slate-900">
    <section class="mx-auto flex w-full max-w-5xl flex-col gap-6 px-6 py-12">
      <Card class="shadow-lg" data-test="search-card">
        <template #title>
          <div class="flex items-center justify-between gap-4">
            <div class="flex items-center gap-3 text-2xl font-semibold">
              <i class="pi pi-search text-emerald-600" aria-hidden="true"></i>
              <span>Search and import books</span>
            </div>
            <NuxtLink to="/library" class="text-sm font-medium text-emerald-700 hover:underline">
              View library
            </NuxtLink>
          </div>
        </template>
        <template #content>
          <div class="flex flex-col gap-4">
            <div class="grid gap-4 md:grid-cols-[1fr_200px]">
              <InputText
                v-model="query"
                class="w-full"
                placeholder="Search Open Library"
                data-test="search-input"
              />
              <Select
                v-model="status"
                :options="statusOptions"
                option-label="label"
                option-value="value"
                data-test="status-select"
              />
            </div>

            <p v-if="hint" class="text-sm text-slate-600" data-test="search-hint">{{ hint }}</p>
            <p
              v-if="error"
              class="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700"
              data-test="search-error"
            >
              {{ error }}
            </p>
            <NuxtLink
              v-if="authRequired"
              :to="loginHref"
              class="text-sm font-medium text-emerald-700 hover:underline"
              data-test="search-login-link"
            >
              Sign in to continue
            </NuxtLink>
            <p
              v-if="message"
              class="rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700"
              data-test="search-message"
            >
              {{ message }}
            </p>

            <div v-if="loading" class="text-sm text-slate-600" data-test="search-loading">
              Searching...
            </div>

            <div v-if="results.length" class="grid gap-3 md:grid-cols-2" data-test="search-results">
              <Card
                v-for="(book, index) in results"
                :key="book.work_key"
                class="border border-slate-200/70"
              >
                <template #content>
                  <div class="flex h-full flex-col gap-3">
                    <div>
                      <p class="text-base font-semibold text-slate-900">{{ book.title }}</p>
                      <p class="text-sm text-slate-600">
                        {{ book.author_names.join(', ') || 'Unknown author' }}
                      </p>
                      <p v-if="book.first_publish_year" class="text-xs text-slate-500">
                        First published: {{ book.first_publish_year }}
                      </p>
                    </div>
                    <Button
                      label="Import and add"
                      class="mt-auto"
                      :loading="importingWorkKey === book.work_key"
                      :data-test="`search-add-${index}`"
                      @click="importAndAdd(book.work_key)"
                    />
                  </div>
                </template>
              </Card>
            </div>
          </div>
        </template>
      </Card>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue';
import { useRoute } from '#imports';
import Button from 'primevue/button';
import Card from 'primevue/card';
import InputText from 'primevue/inputtext';
import Select from 'primevue/select';
import { ApiClientError, apiRequest } from '~/utils/api';

type SearchItem = {
  work_key: string;
  title: string;
  author_names: string[];
  first_publish_year: number | null;
};

const query = ref('');
const status = ref('to_read');
const loading = ref(false);
const results = ref<SearchItem[]>([]);
const error = ref('');
const message = ref('');
const hint = ref('Type at least 2 characters to search.');
const importingWorkKey = ref<string | null>(null);
const authRequired = ref(false);
const route = useRoute();
const loginHref = computed(
  () => `/login?returnTo=${encodeURIComponent(route.fullPath || '/books/search')}`,
);

const statusOptions = [
  { label: 'To read', value: 'to_read' },
  { label: 'Reading', value: 'reading' },
  { label: 'Completed', value: 'completed' },
];

let searchTimer: ReturnType<typeof globalThis.setTimeout> | null = null;

const runSearch = async () => {
  const trimmed = query.value.trim();
  if (trimmed.length < 2) {
    results.value = [];
    hint.value = 'Type at least 2 characters to search.';
    return;
  }

  loading.value = true;
  error.value = '';
  message.value = '';
  hint.value = '';
  authRequired.value = false;

  try {
    const payload = await apiRequest<{ items: SearchItem[] }>('/api/v1/books/search', {
      query: {
        query: trimmed,
        limit: 10,
        page: 1,
      },
    });
    results.value = payload.items;
    if (!payload.items.length) {
      hint.value = 'No books found. Try another search.';
    }
  } catch (err) {
    results.value = [];
    if (err instanceof ApiClientError) {
      error.value = err.message;
      authRequired.value = err.code === 'auth_required';
    } else {
      error.value = 'Unable to search books right now.';
    }
  } finally {
    loading.value = false;
  }
};

const importAndAdd = async (workKey: string) => {
  error.value = '';
  message.value = '';
  authRequired.value = false;
  importingWorkKey.value = workKey;

  try {
    const imported = await apiRequest<{ work: { id: string } }>('/api/v1/books/import', {
      method: 'POST',
      body: { work_key: workKey },
    });

    const libraryResult = await apiRequest<{ created: boolean }>('/api/v1/library/items', {
      method: 'POST',
      body: {
        work_id: imported.work.id,
        status: status.value,
      },
    });

    message.value = libraryResult.created
      ? 'Book imported and added to your library.'
      : 'Book is already in your library.';
  } catch (err) {
    if (err instanceof ApiClientError) {
      error.value = err.message;
      authRequired.value = err.code === 'auth_required';
    } else {
      error.value = 'Unable to import this book right now.';
    }
  } finally {
    importingWorkKey.value = null;
  }
};

watch(query, () => {
  if (searchTimer) {
    globalThis.clearTimeout(searchTimer);
  }
  searchTimer = globalThis.setTimeout(() => {
    void runSearch();
  }, 300);
});

onBeforeUnmount(() => {
  if (searchTimer) {
    globalThis.clearTimeout(searchTimer);
  }
});
</script>
