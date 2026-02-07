<template>
  <div class="min-h-screen bg-slate-950/5 text-slate-900">
    <section class="mx-auto flex w-full max-w-2xl flex-col gap-6 px-6 py-12">
      <Card class="shadow-lg">
        <template #title>
          <div class="flex items-center gap-3 text-2xl font-semibold">
            <i class="pi pi-lock text-emerald-600" aria-hidden="true"></i>
            <span>Authorize access</span>
          </div>
        </template>
        <template #subtitle>
          <span class="text-base text-slate-600">
            Review the request and decide whether to grant access.
          </span>
        </template>
        <template #content>
          <div v-if="loading" class="text-sm text-slate-600">Loading authorization details…</div>
          <div v-else class="flex flex-col gap-4">
            <p v-if="error" class="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {{ error }}
            </p>
            <template v-else>
              <div class="flex items-center gap-3">
                <div
                  v-if="authorization?.client.logo_uri"
                  class="h-12 w-12 overflow-hidden rounded-full border border-slate-200"
                >
                  <img
                    :src="authorization.client.logo_uri"
                    :alt="authorization.client.name || 'Client logo'"
                    class="h-full w-full object-cover"
                  />
                </div>
                <div>
                  <p class="text-lg font-semibold text-slate-900">
                    {{ authorization?.client.name || 'Unnamed application' }}
                  </p>
                  <p class="text-sm text-slate-600">
                    {{ authorization?.client.uri || 'No client URL provided' }}
                  </p>
                </div>
              </div>
              <div>
                <p class="text-sm font-semibold text-slate-800">Requested scopes</p>
                <ul class="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
                  <li v-for="scope in scopes" :key="scope">{{ scope }}</li>
                </ul>
              </div>
              <div>
                <p class="text-sm font-semibold text-slate-800">Redirect URI</p>
                <p class="mt-1 break-all text-sm text-slate-600">
                  {{ authorization?.redirect_uri }}
                </p>
              </div>
            </template>
          </div>
        </template>
        <template #footer>
          <div class="flex flex-wrap items-center gap-3">
            <Button
              label="Approve"
              icon="pi pi-check"
              :loading="submitting"
              :disabled="!authorization || !!error"
              data-test="oauth-approve"
              @click="submitConsent('approve')"
            />
            <Button
              label="Deny"
              severity="secondary"
              icon="pi pi-times"
              :loading="submitting"
              :disabled="!authorization || !!error"
              data-test="oauth-deny"
              @click="submitConsent('deny')"
            />
          </div>
        </template>
      </Card>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { navigateTo, useRoute, useRuntimeConfig, useSupabaseClient } from '#imports';
import Button from 'primevue/button';
import Card from 'primevue/card';

type AuthorizationDetails = {
  authorization_id: string;
  redirect_uri: string;
  scope: string;
  client: {
    id: string;
    name: string | null;
    uri: string | null;
    logo_uri: string | null;
  };
  user: {
    id: string;
    email: string;
  };
};

const supabase = useSupabaseClient();
const config = useRuntimeConfig();
const route = useRoute();

const loading = ref(true);
const submitting = ref(false);
const error = ref('');
const authorization = ref<AuthorizationDetails | null>(null);

const authorizationId = computed(() =>
  typeof route.query.authorization_id === 'string' ? route.query.authorization_id : '',
);

const scopes = computed(() =>
  authorization.value?.scope
    ? authorization.value.scope
        .split(' ')
        .map((item) => item.trim())
        .filter(Boolean)
    : [],
);

const getAccessToken = async () => {
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
};

const fetchAuthorization = async () => {
  if (!authorizationId.value) {
    error.value = 'Missing authorization request.';
    return;
  }

  if (!supabase) {
    error.value = 'Supabase client is not available.';
    return;
  }

  const { data: userData } = await supabase.auth.getUser();
  if (!userData.user) {
    await navigateTo({
      path: '/login',
      query: { returnTo: route.fullPath },
    });
    return;
  }

  const token = await getAccessToken();
  if (!token) {
    await navigateTo({
      path: '/login',
      query: { returnTo: route.fullPath },
    });
    return;
  }

  const supabaseUrl = config.public.supabaseUrl;
  const supabaseAnonKey = config.public.supabaseAnonKey;

  if (!supabaseUrl || !supabaseAnonKey) {
    error.value = 'Supabase configuration is missing.';
    return;
  }

  const response = await globalThis.fetch(
    `${supabaseUrl}/auth/v1/oauth/authorizations/${authorizationId.value}`,
    {
      headers: {
        apikey: supabaseAnonKey,
        Authorization: `Bearer ${token}`,
      },
    },
  );

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    error.value = payload?.message || 'Unable to load authorization details.';
    return;
  }

  authorization.value = (await response.json()) as AuthorizationDetails;
};

const submitConsent = async (action: 'approve' | 'deny') => {
  if (!authorizationId.value || !supabase) {
    return;
  }

  submitting.value = true;
  error.value = '';

  const token = await getAccessToken();
  if (!token) {
    submitting.value = false;
    await navigateTo({
      path: '/login',
      query: { returnTo: route.fullPath },
    });
    return;
  }

  const supabaseUrl = config.public.supabaseUrl;
  const supabaseAnonKey = config.public.supabaseAnonKey;

  if (!supabaseUrl || !supabaseAnonKey) {
    submitting.value = false;
    error.value = 'Supabase configuration is missing.';
    return;
  }

  const response = await globalThis.fetch(
    `${supabaseUrl}/auth/v1/oauth/authorizations/${authorizationId.value}/consent`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        apikey: supabaseAnonKey,
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ action }),
    },
  );

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    submitting.value = false;
    error.value = payload?.message || 'Unable to submit consent.';
    return;
  }

  const payload = (await response.json()) as { redirect_url: string };
  globalThis.location.assign(payload.redirect_url);
};

onMounted(async () => {
  try {
    await fetchAuthorization();
  } finally {
    loading.value = false;
  }
});
</script>
