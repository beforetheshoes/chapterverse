import { mount } from '@vue/test-utils';
import PrimeVue from 'primevue/config';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const authMocks = vi.hoisted(() => ({
  signInWithOtp: vi.fn().mockResolvedValue({ error: null }),
  signInWithOAuth: vi.fn().mockResolvedValue({ error: null }),
}));

const state = vi.hoisted(() => ({
  supabase: { auth: authMocks },
  supabaseState: { value: null },
  supabasePluginLoaded: { value: null },
  config: {
    public: {
      supabaseUrl: 'https://example.supabase.co',
      supabaseAnonKey: 'anon-key',
    },
  },
  route: { query: {}, fullPath: '/login' },
}));

vi.mock('#imports', () => ({
  useNuxtApp: () => ({
    $supabase: state.supabase,
  }),
  useState: (key: string, init?: () => unknown) => {
    const target =
      key === 'supabasePluginLoaded' ? state.supabasePluginLoaded : state.supabaseState;
    if (target.value === null && init) {
      target.value = init();
    }
    return target;
  },
  useRuntimeConfig: () => state.config,
  useRoute: () => ({
    query: state.route.query,
    fullPath: state.route.fullPath,
  }),
}));

import LoginPage from '../../../app/pages/login.vue';

describe('login page', () => {
  beforeEach(() => {
    Object.defineProperty(globalThis, 'location', {
      value: { origin: 'https://staging.theseedbed.app' },
      writable: true,
    });
    state.supabase = { auth: authMocks };
    state.supabaseState.value = state.supabase;
    state.supabasePluginLoaded.value = null;
    state.config = {
      public: {
        supabaseUrl: 'https://example.supabase.co',
        supabaseAnonKey: 'anon-key',
      },
    };
    state.route = { query: {}, fullPath: '/login' };
    authMocks.signInWithOtp.mockClear();
    authMocks.signInWithOtp.mockResolvedValue({ error: null });
    authMocks.signInWithOAuth.mockClear();
    authMocks.signInWithOAuth.mockResolvedValue({ error: null });
  });

  it('submits a magic link request', async () => {
    const wrapper = mount(LoginPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await wrapper.get('[data-test="login-email"]').setValue('reader@theseedbed.app');
    await wrapper.get('[data-test="login-magic-link"]').trigger('click');

    expect(authMocks.signInWithOtp).toHaveBeenCalledWith({
      email: 'reader@theseedbed.app',
      options: {
        emailRedirectTo: expect.any(String),
      },
    });
  });

  it('requires an email before sending a magic link', async () => {
    const wrapper = mount(LoginPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await wrapper.get('[data-test="login-magic-link"]').trigger('click');

    expect(authMocks.signInWithOtp).not.toHaveBeenCalled();
    expect(wrapper.text()).toContain('Enter a valid email address.');
  });

  it('shows an error when magic link request fails', async () => {
    authMocks.signInWithOtp.mockResolvedValueOnce({ error: { message: 'Nope' } });

    const wrapper = mount(LoginPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await wrapper.get('[data-test="login-email"]').setValue('reader@theseedbed.app');
    await wrapper.get('[data-test="login-magic-link"]').trigger('click');

    expect(wrapper.text()).toContain('Nope');
  });

  it('builds a redirect that preserves returnTo', async () => {
    state.route = {
      query: { returnTo: '/oauth/consent?authorization_id=auth-123' },
      fullPath: '/login?returnTo=/oauth/consent?authorization_id=auth-123',
    };

    const wrapper = mount(LoginPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await wrapper.get('[data-test="login-email"]').setValue('reader@theseedbed.app');
    await wrapper.get('[data-test="login-magic-link"]').trigger('click');

    const call = authMocks.signInWithOtp.mock.calls[0]?.[0];
    const redirectUrl = new globalThis.URL(call.options.emailRedirectTo);

    expect(redirectUrl.pathname).toBe('/auth/callback');
    expect(redirectUrl.searchParams.get('returnTo')).toBe(
      '/oauth/consent?authorization_id=auth-123',
    );
  });

  it('starts Apple OAuth sign-in', async () => {
    const wrapper = mount(LoginPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await wrapper.get('[data-test="login-apple"]').trigger('click');

    expect(authMocks.signInWithOAuth).toHaveBeenCalledWith({
      provider: 'apple',
      options: {
        redirectTo: expect.any(String),
      },
    });
  });

  it('shows an error when Supabase is unavailable for magic links', async () => {
    state.supabase = null;
    state.supabaseState.value = null;

    const wrapper = mount(LoginPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await wrapper.get('[data-test="login-email"]').setValue('reader@theseedbed.app');
    await wrapper.get('[data-test="login-magic-link"]').trigger('click');

    expect(authMocks.signInWithOtp).not.toHaveBeenCalled();
    expect(wrapper.text()).toContain('Supabase client is not available.');
  });

  it('shows an error when Apple OAuth fails', async () => {
    authMocks.signInWithOAuth.mockResolvedValueOnce({ error: { message: 'Apple down' } });

    const wrapper = mount(LoginPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await wrapper.get('[data-test="login-apple"]').trigger('click');

    expect(wrapper.text()).toContain('Apple down');
  });

  it('falls back when Supabase client is missing', async () => {
    state.supabase = null;
    state.supabaseState.value = null;

    const wrapper = mount(LoginPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await wrapper.get('[data-test="login-apple"]').trigger('click');

    expect(wrapper.text()).toContain('Supabase client is not available.');
  });

  it('builds an empty redirect when origin is unavailable', async () => {
    Object.defineProperty(globalThis, 'location', {
      value: undefined,
      writable: true,
    });

    const wrapper = mount(LoginPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await wrapper.get('[data-test="login-email"]').setValue('reader@theseedbed.app');
    await wrapper.get('[data-test="login-magic-link"]').trigger('click');

    expect(authMocks.signInWithOtp).toHaveBeenCalledWith({
      email: 'reader@theseedbed.app',
      options: {
        emailRedirectTo: '',
      },
    });
  });

  it('builds an empty redirect when origin is blank', async () => {
    Object.defineProperty(globalThis, 'location', {
      value: {
        origin: '',
        hostname: 'preview.vercel.app',
      },
      writable: true,
    });

    const wrapper = mount(LoginPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await wrapper.get('[data-test="login-email"]').setValue('reader@theseedbed.app');
    await wrapper.get('[data-test="login-magic-link"]').trigger('click');

    expect(authMocks.signInWithOtp).toHaveBeenCalledWith({
      email: 'reader@theseedbed.app',
      options: {
        emailRedirectTo: '',
      },
    });
  });

  it('shows a debug banner on preview hosts', async () => {
    state.supabasePluginLoaded.value = true;
    Object.defineProperty(globalThis, 'location', {
      value: {
        origin: 'https://preview.vercel.app',
        hostname: 'preview.vercel.app',
      },
      writable: true,
    });

    const wrapper = mount(LoginPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    expect(wrapper.text()).toContain('Preview debug:');
    expect(wrapper.text()).toContain('supabaseUrl=set');
    expect(wrapper.text()).toContain('supabaseAnonKey=set');
    expect(wrapper.text()).toContain('client=ready');
    expect(wrapper.text()).toContain('plugin=loaded');
  });

  it('shows missing debug flags when config is unavailable', async () => {
    state.supabase = null;
    state.supabaseState.value = null;
    state.supabasePluginLoaded.value = false;
    state.config = {
      public: {
        supabaseUrl: '',
        supabaseAnonKey: '',
      },
    };
    Object.defineProperty(globalThis, 'location', {
      value: {
        origin: 'https://preview.vercel.app',
        hostname: 'preview.vercel.app',
      },
      writable: true,
    });

    const wrapper = mount(LoginPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    expect(wrapper.text()).toContain('supabaseUrl=missing');
    expect(wrapper.text()).toContain('supabaseAnonKey=missing');
    expect(wrapper.text()).toContain('client=missing');
    expect(wrapper.text()).toContain('plugin=missing');
  });

  it('skips the debug banner on production hosts', async () => {
    Object.defineProperty(globalThis, 'location', {
      value: {
        origin: 'https://theseedbed.app',
        hostname: 'theseedbed.app',
      },
      writable: true,
    });

    const wrapper = mount(LoginPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    expect(wrapper.text()).not.toContain('Preview debug:');
  });
});
