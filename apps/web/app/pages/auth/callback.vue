<template>
  <div class="min-h-screen bg-slate-950/5 text-slate-900">
    <section class="mx-auto flex w-full max-w-lg flex-col gap-4 px-6 py-16 text-center">
      <i class="pi pi-spinner pi-spin text-3xl text-emerald-600" aria-hidden="true"></i>
      <h1 class="text-2xl font-semibold">Finishing sign-in</h1>
      <p class="text-sm text-slate-600">
        {{ message }}
      </p>
      <p v-if="error" class="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">
        {{ error }}
      </p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { navigateTo, useRoute, useState } from '#imports';
import type { SupabaseClient } from '@supabase/supabase-js';

const supabase = useState<SupabaseClient | null>('supabase', () => null);
const route = useRoute();

const message = ref('Validating your session…');
const error = ref('');

const resolveReturnTo = () =>
  typeof route.query.returnTo === 'string' && route.query.returnTo ? route.query.returnTo : '/';

onMounted(async () => {
  if (!supabase.value) {
    error.value = 'Supabase client is not available.';
    return;
  }

  const returnTo = resolveReturnTo();

  const { data, error: sessionError } = await supabase.value.auth.getSession();
  if (sessionError) {
    error.value = sessionError.message;
    return;
  }

  if (data.session) {
    await navigateTo(returnTo);
    return;
  }

  message.value = 'Waiting for authentication to complete…';

  const { data: authListener } = supabase.value.auth.onAuthStateChange(async (_event, session) => {
    if (session) {
      authListener.subscription.unsubscribe();
      await navigateTo(returnTo);
    }
  });

  globalThis.setTimeout(() => {
    if (!error.value) {
      error.value = 'Session not found. Try signing in again.';
      authListener.subscription.unsubscribe();
    }
  }, 6000);
});
</script>
