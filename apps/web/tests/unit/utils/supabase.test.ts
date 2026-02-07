import { describe, expect, it, vi } from 'vitest';

const createClientMock = vi.hoisted(() => vi.fn(() => ({ mocked: true })));

vi.mock('@supabase/supabase-js', () => ({
  createClient: createClientMock,
}));

import { createSupabaseClient } from '~/utils/supabase';

describe('createSupabaseClient', () => {
  it('creates a client when config is present', () => {
    const client = createSupabaseClient({
      url: 'https://example.supabase.co',
      anonKey: 'anon-key',
    });

    expect(createClientMock).toHaveBeenCalledWith('https://example.supabase.co', 'anon-key');
    expect(client).toEqual({ mocked: true });
  });

  it('throws when the URL is missing', () => {
    expect(() =>
      createSupabaseClient({
        url: undefined,
        anonKey: 'anon-key',
      }),
    ).toThrow('Supabase URL and anon key are required');
  });

  it('throws when the anon key is missing', () => {
    expect(() =>
      createSupabaseClient({
        url: 'https://example.supabase.co',
        anonKey: undefined,
      }),
    ).toThrow('Supabase URL and anon key are required');
  });
});
