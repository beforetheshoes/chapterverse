import { beforeEach, describe, expect, it, vi } from 'vitest';

const state = {
  config: {
    public: {
      supabaseUrl: '',
      supabaseAnonKey: '',
    },
  },
  supabaseState: { value: null as unknown },
  pluginState: { value: null as unknown },
};

const createSupabaseClient = vi.hoisted(() => vi.fn(() => ({ mock: true })));

vi.mock('~/utils/supabase', () => ({
  createSupabaseClient,
}));

vi.mock('#imports', () => ({
  defineNuxtPlugin: (plugin: () => unknown) => plugin,
  useRuntimeConfig: () => state.config,
  useState: (key: string, init?: () => unknown) => {
    const target = key === 'supabasePluginLoaded' ? state.pluginState : state.supabaseState;
    if (target.value === null && init) {
      target.value = init();
    }
    return target;
  },
}));

import supabasePlugin from '../../../app/plugins/supabase.client';

describe('supabase client plugin', () => {
  beforeEach(() => {
    state.config = {
      public: {
        supabaseUrl: '',
        supabaseAnonKey: '',
      },
    };
    state.supabaseState.value = null;
    state.pluginState.value = null;
    createSupabaseClient.mockClear();
  });

  it('initializes the Supabase client when config is present', () => {
    state.config = {
      public: {
        supabaseUrl: 'https://example.supabase.co',
        supabaseAnonKey: 'anon-key',
      },
    };

    const result = supabasePlugin() as {
      provide: { supabase: { mock: boolean } | null };
    };

    expect(createSupabaseClient).toHaveBeenCalledWith({
      url: 'https://example.supabase.co',
      anonKey: 'anon-key',
    });
    expect(result.provide.supabase).toEqual({ mock: true });
    expect(state.supabaseState.value).toEqual({ mock: true });
    expect(state.pluginState.value).toBe(true);
  });

  it('warns and leaves supabase null when config is missing', () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => undefined);

    const result = supabasePlugin() as {
      provide: { supabase: null };
    };

    expect(createSupabaseClient).not.toHaveBeenCalled();
    expect(result.provide.supabase).toBeNull();
    expect(state.supabaseState.value).toBeNull();
    expect(state.pluginState.value).toBe(true);
    expect(warnSpy).toHaveBeenCalledWith('Supabase env vars missing; client was not initialized.');

    warnSpy.mockRestore();
  });
});
