import type { SupabaseClient } from '@supabase/supabase-js';
import { useRuntimeConfig, useSupabaseClient } from '#imports';

type Envelope<T> = {
  data: T | null;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown> | null;
  } | null;
};

export class ApiClientError extends Error {
  code: string;
  status?: number;

  constructor(message: string, code: string, status?: number) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

const getApiBaseUrl = (): string => {
  const config = useRuntimeConfig();
  const value = config.public.apiBaseUrl;
  if (typeof value === 'string' && value.trim()) {
    return value.replace(/\/$/, '');
  }
  return 'http://localhost:8000';
};

const getAccessToken = async (): Promise<string> => {
  const supabase = useSupabaseClient<SupabaseClient | null>();
  if (!supabase) {
    throw new ApiClientError('Sign in is required to use the API.', 'auth_required', 401);
  }

  const {
    data: { session },
  } = await supabase.auth.getSession();

  const token = session?.access_token;
  if (!token) {
    throw new ApiClientError('Sign in is required to use the API.', 'auth_required', 401);
  }

  return token;
};

export const apiRequest = async <T>(
  path: string,
  options?: {
    method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
    query?: Record<string, string | number | undefined | null>;
    body?: unknown;
  },
): Promise<T> => {
  const baseUrl = getApiBaseUrl();
  const token = await getAccessToken();

  const url = new globalThis.URL(`${baseUrl}${path}`);
  for (const [key, value] of Object.entries(options?.query ?? {})) {
    if (value === undefined || value === null || value === '') {
      continue;
    }
    url.searchParams.set(key, String(value));
  }

  const response = await globalThis.fetch(url.toString(), {
    method: options?.method ?? 'GET',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: options?.body ? JSON.stringify(options.body) : undefined,
  });

  const payload = (await response.json()) as Envelope<T>;
  if (!response.ok || payload.error) {
    throw new ApiClientError(
      payload.error?.message ?? 'Request failed.',
      payload.error?.code ?? 'request_failed',
      response.status,
    );
  }

  if (payload.data === null) {
    throw new ApiClientError('Missing response payload.', 'invalid_response', response.status);
  }

  return payload.data;
};
