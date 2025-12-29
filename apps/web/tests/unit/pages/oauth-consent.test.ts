import { flushPromises, mount } from '@vue/test-utils';
import PrimeVue from 'primevue/config';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const authMocks = vi.hoisted(() => ({
  getUser: vi.fn().mockResolvedValue({
    data: { user: { id: 'user-1', email: 'reader@theseedbed.app' } },
  }),
  getSession: vi.fn().mockResolvedValue({
    data: { session: { access_token: 'token-123' } },
  }),
}));

const navigateToMock = vi.hoisted(() => vi.fn());

const state = vi.hoisted(() => ({
  supabase: { auth: authMocks },
  supabaseState: { value: null },
  config: {
    public: {
      supabaseUrl: 'https://example.supabase.co',
      supabaseAnonKey: 'anon-key',
    },
  },
  route: {
    query: { authorization_id: 'auth-123' },
    fullPath: '/oauth/consent?authorization_id=auth-123',
  },
}));

vi.mock('#imports', () => ({
  useNuxtApp: () => ({
    $supabase: state.supabase,
  }),
  useState: (_key: string, init?: () => unknown) => {
    if (state.supabaseState.value === null && init) {
      state.supabaseState.value = init();
    }
    return state.supabaseState;
  },
  useRuntimeConfig: () => state.config,
  useRoute: () => state.route,
  navigateTo: navigateToMock,
}));

import ConsentPage from '../../../app/pages/oauth/consent.vue';

describe('oauth consent page', () => {
  beforeEach(() => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        authorization_id: 'auth-123',
        redirect_uri: 'https://theseedbed.app/oauth/callback',
        scope: 'profile.read library.read',
        client: {
          id: 'client-1',
          name: 'The Seedbed',
          uri: 'https://theseedbed.app',
          logo_uri: null,
        },
        user: {
          id: 'user-1',
          email: 'reader@theseedbed.app',
        },
      }),
    }) as typeof globalThis.fetch;

    state.supabase = { auth: authMocks };
    state.supabaseState.value = state.supabase;
    state.config = {
      public: {
        supabaseUrl: 'https://example.supabase.co',
        supabaseAnonKey: 'anon-key',
      },
    };
    state.route = {
      query: { authorization_id: 'auth-123' },
      fullPath: '/oauth/consent?authorization_id=auth-123',
    };
    authMocks.getUser.mockResolvedValue({
      data: { user: { id: 'user-1', email: 'reader@theseedbed.app' } },
    });
    authMocks.getSession.mockResolvedValue({
      data: { session: { access_token: 'token-123' } },
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders authorization details', async () => {
    const wrapper = mount(ConsentPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await flushPromises();

    expect(wrapper.text()).toContain('The Seedbed');
    expect(wrapper.text()).toContain('profile.read');
    expect(wrapper.text()).toContain('library.read');
    expect(navigateToMock).not.toHaveBeenCalled();
  });

  it('shows an error when authorization_id is missing', async () => {
    state.route = { query: {}, fullPath: '/oauth/consent' };

    const wrapper = mount(ConsentPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await flushPromises();

    expect(wrapper.text()).toContain('Missing authorization request.');
  });

  it('redirects to login when user is not authenticated', async () => {
    authMocks.getUser.mockResolvedValueOnce({ data: { user: null } });

    const wrapper = mount(ConsentPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await flushPromises();

    expect(wrapper.text()).toContain('Authorize access');
    expect(navigateToMock).toHaveBeenCalledWith({
      path: '/login',
      query: { returnTo: '/oauth/consent?authorization_id=auth-123' },
    });
  });

  it('shows an error when Supabase client is missing', async () => {
    state.supabase = null;
    state.supabaseState.value = null;

    const wrapper = mount(ConsentPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await flushPromises();

    expect(wrapper.text()).toContain('Supabase client is not available.');
  });

  it('shows an error when Supabase config is missing', async () => {
    state.config.public.supabaseUrl = '';

    const wrapper = mount(ConsentPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await flushPromises();

    expect(wrapper.text()).toContain('Supabase configuration is missing.');
  });

  it('handles authorization fetch errors', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ message: 'nope' }),
    }) as typeof globalThis.fetch;

    const wrapper = mount(ConsentPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await flushPromises();

    expect(wrapper.text()).toContain('nope');
  });

  it('falls back when authorization error payload is missing', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      json: async () => {
        throw new Error('boom');
      },
    }) as typeof globalThis.fetch;

    const wrapper = mount(ConsentPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await flushPromises();

    expect(wrapper.text()).toContain('Unable to load authorization details.');
  });

  it('does nothing when authorization_id is missing during consent submit', async () => {
    state.route = { query: {}, fullPath: '/oauth/consent' };

    const wrapper = mount(ConsentPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await flushPromises();

    const vm = wrapper.vm as {
      // eslint-disable-next-line no-unused-vars
      submitConsent?: (action: 'approve' | 'deny') => Promise<void>;
    };
    await vm.submitConsent?.('approve');

    expect(globalThis.fetch).not.toHaveBeenCalled();
  });

  it('shows an error when consent submit config is missing', async () => {
    const wrapper = mount(ConsentPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await flushPromises();
    state.config.public.supabaseUrl = '';

    await wrapper.get('[data-test="oauth-approve"]').trigger('click');
    await flushPromises();

    expect(wrapper.text()).toContain('Supabase configuration is missing.');
  });

  it('shows an error when consent submission fails', async () => {
    const fetchMock = vi.fn();
    fetchMock
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          authorization_id: 'auth-123',
          redirect_uri: 'https://theseedbed.app/oauth/callback',
          scope: 'profile.read',
          client: {
            id: 'client-1',
            name: 'The Seedbed',
            uri: 'https://theseedbed.app',
            logo_uri: null,
          },
          user: {
            id: 'user-1',
            email: 'reader@theseedbed.app',
          },
        }),
      })
      .mockResolvedValueOnce({
        ok: false,
        json: async () => ({ message: 'consent denied' }),
      });

    globalThis.fetch = fetchMock as typeof globalThis.fetch;

    const wrapper = mount(ConsentPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await flushPromises();
    await wrapper.get('[data-test="oauth-approve"]').trigger('click');
    await flushPromises();

    expect(wrapper.text()).toContain('consent denied');
  });

  it('falls back when consent error payload is missing', async () => {
    const fetchMock = vi.fn();
    fetchMock
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          authorization_id: 'auth-123',
          redirect_uri: 'https://theseedbed.app/oauth/callback',
          scope: 'profile.read',
          client: {
            id: 'client-1',
            name: 'The Seedbed',
            uri: 'https://theseedbed.app',
            logo_uri: null,
          },
          user: {
            id: 'user-1',
            email: 'reader@theseedbed.app',
          },
        }),
      })
      .mockResolvedValueOnce({
        ok: false,
        json: async () => {
          throw new Error('boom');
        },
      });

    globalThis.fetch = fetchMock as typeof globalThis.fetch;

    const wrapper = mount(ConsentPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await flushPromises();
    await wrapper.get('[data-test="oauth-approve"]').trigger('click');
    await flushPromises();

    expect(wrapper.text()).toContain('Unable to submit consent.');
  });

  it('redirects to login when access token is missing', async () => {
    authMocks.getSession.mockResolvedValueOnce({ data: { session: null } });

    mount(ConsentPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await flushPromises();

    expect(navigateToMock).toHaveBeenCalledWith({
      path: '/login',
      query: { returnTo: '/oauth/consent?authorization_id=auth-123' },
    });
  });

  it('submits a deny consent and redirects', async () => {
    const fetchMock = vi.fn();
    fetchMock
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          authorization_id: 'auth-123',
          redirect_uri: 'https://theseedbed.app/oauth/callback',
          scope: 'profile.read',
          client: {
            id: 'client-1',
            name: 'The Seedbed',
            uri: 'https://theseedbed.app',
            logo_uri: null,
          },
          user: {
            id: 'user-1',
            email: 'reader@theseedbed.app',
          },
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ redirect_url: 'https://theseedbed.app/callback?code=1' }),
      });

    globalThis.fetch = fetchMock as typeof globalThis.fetch;
    const assignMock = vi.fn();
    Object.defineProperty(globalThis, 'location', {
      value: { assign: assignMock },
      writable: true,
    });

    const wrapper = mount(ConsentPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await flushPromises();
    await wrapper.get('[data-test="oauth-deny"]').trigger('click');
    await flushPromises();

    expect(assignMock).toHaveBeenCalledWith('https://theseedbed.app/callback?code=1');
  });

  it('redirects to login when session token is missing', async () => {
    authMocks.getSession
      .mockResolvedValueOnce({
        data: { session: { access_token: 'token-123' } },
      })
      .mockResolvedValueOnce({ data: { session: null } });

    const wrapper = mount(ConsentPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await flushPromises();
    await wrapper.get('[data-test="oauth-approve"]').trigger('click');
    await flushPromises();

    expect(navigateToMock).toHaveBeenCalledWith({
      path: '/login',
      query: { returnTo: '/oauth/consent?authorization_id=auth-123' },
    });
  });
});
