<template>
  <div class="min-h-screen bg-slate-950/5 text-slate-900">
    <section class="mx-auto flex w-full max-w-lg flex-col gap-6 px-6 py-12">
      <Card class="shadow-lg">
        <template #title>
          <div class="flex items-center gap-3 text-2xl font-semibold">
            <i class="pi pi-book text-emerald-600" aria-hidden="true"></i>
            <span>Sign in to The Seedbed</span>
          </div>
        </template>
        <template #subtitle>
          <span class="text-base text-slate-600">
            Use Apple or request a magic link to continue.
          </span>
        </template>
        <template #content>
          <div class="flex flex-col gap-4">
            <Button
              class="w-full"
              icon="pi pi-apple"
              label="Continue with Apple"
              :loading="busy"
              data-test="login-apple"
              @click="signInWithApple"
            />
            <div class="flex items-center gap-3">
              <div class="h-px flex-1 bg-slate-200"></div>
              <span class="text-xs uppercase tracking-[0.2em] text-slate-400">or</span>
              <div class="h-px flex-1 bg-slate-200"></div>
            </div>
            <div class="flex flex-col gap-2">
              <label class="text-sm font-medium text-slate-700" for="email">Email</label>
              <InputText
                id="email"
                v-model="email"
                class="w-full"
                type="email"
                placeholder="you@theseedbed.app"
                data-test="login-email"
              />
            </div>
            <Button
              class="w-full"
              label="Send magic link"
              :loading="busy"
              data-test="login-magic-link"
              @click="sendMagicLink"
            />
            <p v-if="status" class="rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
              {{ status }}
            </p>
            <p v-if="error" class="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {{ error }}
            </p>
            <p v-if="!supabase" class="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700">
              Supabase client is not configured. Check environment variables.
            </p>
          </div>
        </template>
      </Card>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useNuxtApp, useRoute } from '#imports';
import type { SupabaseClient } from '@supabase/supabase-js';
import Button from 'primevue/button';
import Card from 'primevue/card';
import InputText from 'primevue/inputtext';

const { $supabase } = useNuxtApp();
const supabase = $supabase as SupabaseClient | null;
const route = useRoute();

const email = ref('');
const busy = ref(false);
const status = ref('');
const error = ref('');

const returnTo = computed(() =>
  typeof route.query.returnTo === 'string' ? route.query.returnTo : '',
);

const buildRedirectTo = () => {
  if (typeof window === 'undefined') {
    return '';
  }

  const origin = globalThis.location?.origin;
  if (!origin) {
    return '';
  }

  const base = `${origin}/auth/callback`;
  if (!returnTo.value) {
    return base;
  }

  const redirectUrl = new globalThis.URL(base);
  redirectUrl.searchParams.set('returnTo', returnTo.value);
  return redirectUrl.toString();
};

const sendMagicLink = async () => {
  status.value = '';
  error.value = '';

  if (!supabase) {
    error.value = 'Supabase client is not available.';
    return;
  }

  if (!email.value.trim()) {
    error.value = 'Enter a valid email address.';
    return;
  }

  busy.value = true;

  const redirectTo = buildRedirectTo();
  const { error: signInError } = await supabase.auth.signInWithOtp({
    email: email.value.trim(),
    options: {
      emailRedirectTo: redirectTo,
    },
  });

  busy.value = false;

  if (signInError) {
    error.value = signInError.message;
    return;
  }

  status.value = 'Check your inbox for the magic link.';
};

const signInWithApple = async () => {
  status.value = '';
  error.value = '';

  if (!supabase) {
    error.value = 'Supabase client is not available.';
    return;
  }

  busy.value = true;
  const redirectTo = buildRedirectTo();
  const { error: signInError } = await supabase.auth.signInWithOAuth({
    provider: 'apple',
    options: {
      redirectTo,
    },
  });

  busy.value = false;

  if (signInError) {
    error.value = signInError.message;
  }
};
</script>
