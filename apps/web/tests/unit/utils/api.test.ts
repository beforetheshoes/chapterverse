import { beforeEach, describe, expect, it, vi } from 'vitest';

const state = vi.hoisted(() => ({
  supabaseClient: null as any,
  config: { public: { apiBaseUrl: 'http://localhost:8000' } },
}));

vi.mock('#imports', () => ({
  useRuntimeConfig: () => state.config,
  useSupabaseClient: () => state.supabaseClient,
}));

import { ApiClientError, apiRequest } from '../../../app/utils/api';

describe('api utils', () => {
  beforeEach(() => {
    state.supabaseClient = null;
    state.config = { public: { apiBaseUrl: 'http://localhost:8000' } };
  });

  it('throws auth_required when no supabase client is present', async () => {
    await expect(apiRequest('/api/v1/me')).rejects.toMatchObject({ code: 'auth_required' });
  });

  it('throws auth_required when session token is missing', async () => {
    state.supabaseClient = {
      auth: {
        getSession: vi.fn().mockResolvedValue({ data: { session: null } }),
      },
    };

    await expect(apiRequest('/api/v1/me')).rejects.toMatchObject({ code: 'auth_required' });
  });

  it('sends bearer token and returns response data', async () => {
    state.supabaseClient = {
      auth: {
        getSession: vi.fn().mockResolvedValue({
          data: { session: { access_token: 'token-123' } },
        }),
      },
    };

    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ data: { ok: true }, error: null }),
    } as any);

    const data = await apiRequest<{ ok: boolean }>('/api/v1/me', {
      query: { include: 'profile', skip: undefined, none: null, empty: '' },
    });

    expect(data.ok).toBe(true);
    const [url, options] = fetchMock.mock.calls[0] as [string, any];
    expect(url).toContain('/api/v1/me?include=profile');
    expect(url).not.toContain('skip=');
    expect(options.headers).toEqual(expect.objectContaining({ Authorization: 'Bearer token-123' }));

    fetchMock.mockRestore();
  });

  it('includes request body when provided', async () => {
    state.supabaseClient = {
      auth: {
        getSession: vi.fn().mockResolvedValue({
          data: { session: { access_token: 'token-123' } },
        }),
      },
    };

    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ data: { ok: true }, error: null }),
    } as any);

    await apiRequest('/api/v1/books/import', {
      method: 'POST',
      body: { work_key: '/works/OL1W' },
    });

    const [, options] = fetchMock.mock.calls[0] as [string, any];
    expect(options.body).toBe(JSON.stringify({ work_key: '/works/OL1W' }));
    fetchMock.mockRestore();
  });

  it('falls back to localhost base url when config is unset', async () => {
    state.config = { public: { apiBaseUrl: '' } };
    state.supabaseClient = {
      auth: {
        getSession: vi.fn().mockResolvedValue({
          data: { session: { access_token: 'token-123' } },
        }),
      },
    };

    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ data: { ok: true }, error: null }),
    } as any);

    await apiRequest('/api/v1/me');
    expect(fetchMock.mock.calls[0]?.[0]).toContain('http://localhost:8000/api/v1/me');
    fetchMock.mockRestore();
  });

  it('throws api error when response includes envelope error', async () => {
    state.supabaseClient = {
      auth: {
        getSession: vi.fn().mockResolvedValue({
          data: { session: { access_token: 'token-123' } },
        }),
      },
    };

    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ data: null, error: { code: 'bad', message: 'Nope' } }),
    } as any);

    const promise = apiRequest('/api/v1/me');
    await expect(promise).rejects.toBeInstanceOf(ApiClientError);
    await expect(promise).rejects.toMatchObject({
      code: 'bad',
      message: 'Nope',
      status: 400,
    });

    fetchMock.mockRestore();
  });

  it('falls back to default error code/message when envelope error is missing', async () => {
    state.supabaseClient = {
      auth: {
        getSession: vi.fn().mockResolvedValue({
          data: { session: { access_token: 'token-123' } },
        }),
      },
    };

    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({ data: null, error: null }),
    } as any);

    await expect(apiRequest('/api/v1/me')).rejects.toMatchObject({
      code: 'request_failed',
      message: 'Request failed.',
      status: 500,
    });
    fetchMock.mockRestore();
  });

  it('throws invalid_response when envelope is missing data', async () => {
    state.supabaseClient = {
      auth: {
        getSession: vi.fn().mockResolvedValue({
          data: { session: { access_token: 'token-123' } },
        }),
      },
    };

    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ data: null, error: null }),
    } as any);

    await expect(apiRequest('/api/v1/me')).rejects.toMatchObject({ code: 'invalid_response' });
    fetchMock.mockRestore();
  });
});
