import { createClient } from '@supabase/supabase-js';
import type { SupabaseClient } from '@supabase/supabase-js';

type SupabaseConfig = {
  url: string | undefined;
  anonKey: string | undefined;
};

export const createSupabaseClient = ({ url, anonKey }: SupabaseConfig): SupabaseClient => {
  if (!url || !anonKey) {
    throw new Error('Supabase URL and anon key are required');
  }

  return createClient(url, anonKey);
};
