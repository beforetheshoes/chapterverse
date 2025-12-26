import { createSupabaseClient } from '~/utils/supabase';

export default defineNuxtPlugin(() => {
  const config = useRuntimeConfig();
  const { supabaseUrl, supabaseAnonKey } = config.public;
  const supabase =
    supabaseUrl && supabaseAnonKey
      ? createSupabaseClient({ url: supabaseUrl, anonKey: supabaseAnonKey })
      : null;

  if (!supabase) {
    console.warn('Supabase env vars missing; client was not initialized.');
  }

  return {
    provide: {
      supabase,
    },
  };
});
