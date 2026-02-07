<template>
  <div class="min-h-screen bg-slate-950/5 text-slate-900">
    <section class="mx-auto flex w-full max-w-5xl flex-col gap-6 px-6 py-12">
      <Card class="shadow-lg" data-test="library-card">
        <template #title>
          <div class="flex items-center justify-between gap-4">
            <div class="flex items-center gap-3 text-2xl font-semibold">
              <i class="pi pi-book text-emerald-600" aria-hidden="true"></i>
              <span>Your library</span>
            </div>
            <NuxtLink
              to="/books/search"
              class="text-sm font-medium text-emerald-700 hover:underline"
            >
              Add books
            </NuxtLink>
          </div>
        </template>
        <template #content>
          <div class="flex flex-col gap-4">
            <div class="grid gap-4 md:grid-cols-[240px_1fr]">
              <Select
                v-model="statusFilter"
                :options="statusFilters"
                option-label="label"
                option-value="value"
                data-test="library-status-filter"
              />
            </div>

            <p
              v-if="error"
              class="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700"
              data-test="library-error"
            >
              {{ error }}
            </p>
            <NuxtLink
              v-if="authRequired"
              :to="loginHref"
              class="text-sm font-medium text-emerald-700 hover:underline"
              data-test="library-login-link"
            >
              Sign in to continue
            </NuxtLink>

            <div v-if="loading" class="text-sm text-slate-600" data-test="library-loading">
              Loading...
            </div>

            <div v-if="items.length" class="grid gap-3" data-test="library-items">
              <Card v-for="item in items" :key="item.id" class="border border-slate-200/70">
                <template #content>
                  <div class="flex items-center justify-between gap-3">
                    <div>
                      <p class="font-semibold text-slate-900">{{ item.work_title }}</p>
                      <p class="text-sm text-slate-600">Status: {{ item.status }}</p>
                    </div>
                    <span class="rounded bg-slate-100 px-2 py-1 text-xs uppercase text-slate-600">
                      {{ item.visibility }}
                    </span>
                  </div>
                </template>
              </Card>
            </div>

            <p v-else-if="!loading" class="text-sm text-slate-600" data-test="library-empty">
              No library items found.
            </p>

            <Button
              v-if="nextCursor"
              label="Load more"
              class="self-start"
              :loading="loadingMore"
              data-test="library-load-more"
              @click="loadMore"
            />
          </div>
        </template>
      </Card>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute } from '#imports';
import Button from 'primevue/button';
import Card from 'primevue/card';
import Select from 'primevue/select';
import { ApiClientError, apiRequest } from '~/utils/api';

type LibraryItem = {
  id: string;
  work_id: string;
  work_title: string;
  status: string;
  visibility: string;
};

const items = ref<LibraryItem[]>([]);
const statusFilter = ref<string>('');
const nextCursor = ref<string | null>(null);
const loading = ref(false);
const loadingMore = ref(false);
const error = ref('');
const authRequired = ref(false);
const route = useRoute();
const loginHref = computed(
  () => `/login?returnTo=${encodeURIComponent(route.fullPath || '/library')}`,
);

const statusFilters = [
  { label: 'All statuses', value: '' },
  { label: 'To read', value: 'to_read' },
  { label: 'Reading', value: 'reading' },
  { label: 'Completed', value: 'completed' },
];

const fetchPage = async (append = false) => {
  error.value = '';
  authRequired.value = false;
  if (append) {
    loadingMore.value = true;
  } else {
    loading.value = true;
  }

  try {
    const payload = await apiRequest<{ items: LibraryItem[]; next_cursor: string | null }>(
      '/api/v1/library/items',
      {
        query: {
          limit: 10,
          cursor: append ? nextCursor.value : undefined,
          status: statusFilter.value || undefined,
        },
      },
    );

    items.value = append ? [...items.value, ...payload.items] : payload.items;
    nextCursor.value = payload.next_cursor;
  } catch (err) {
    if (err instanceof ApiClientError) {
      error.value = err.message;
      authRequired.value = err.code === 'auth_required';
    } else {
      error.value = 'Unable to load library items right now.';
    }
  } finally {
    loading.value = false;
    loadingMore.value = false;
  }
};

const loadMore = async () => {
  await fetchPage(true);
};

watch(statusFilter, () => {
  void fetchPage(false);
});

onMounted(() => {
  void fetchPage(false);
});
</script>
