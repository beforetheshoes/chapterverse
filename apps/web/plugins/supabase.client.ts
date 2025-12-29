import { createSupabaseClient } from '~/utils/supabase';
import { useState } from '#imports';

export default defineNuxtPlugin(() => {
  const config = useRuntimeConfig();
  const { supabaseUrl, supabaseAnonKey } = config.public;
  const supabaseState = useState<ReturnType<typeof createSupabaseClient> | null>(
    'supabase',
    () => null,
  );
  const supabase =
    supabaseUrl && supabaseAnonKey
      ? createSupabaseClient({ url: supabaseUrl, anonKey: supabaseAnonKey })
      : null;

  if (!supabase) {
    console.warn('Supabase env vars missing; client was not initialized.');
  }

  supabaseState.value = supabase;

  return {
    provide: {
      supabase,
    },
  };
});
