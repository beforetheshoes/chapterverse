import { flushPromises, mount } from '@vue/test-utils';
import PrimeVue from 'primevue/config';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const authMocks = vi.hoisted(() => ({
  getSession: vi.fn().mockResolvedValue({
    data: { session: { access_token: 'token-123' } },
    error: null,
  }),
  onAuthStateChange: vi.fn().mockReturnValue({
    data: {
      subscription: {
        unsubscribe: vi.fn(),
      },
    },
  }),
}));

const navigateToMock = vi.hoisted(() => vi.fn());

const state = vi.hoisted(() => ({
  supabase: { auth: authMocks },
  route: { query: { returnTo: '/oauth/consent?authorization_id=auth-123' } },
}));

vi.mock('#imports', () => ({
  useSupabaseClient: () => state.supabase,
  useRoute: () => ({
    query: state.route.query,
  }),
  navigateTo: navigateToMock,
}));

import CallbackPage from '../../../app/pages/auth/callback.vue';

describe('auth callback page', () => {
  beforeEach(() => {
    state.supabase = { auth: authMocks };
    state.route = { query: { returnTo: '/oauth/consent?authorization_id=auth-123' } };
    navigateToMock.mockClear();
    authMocks.getSession.mockResolvedValue({
      data: { session: { access_token: 'token-123' } },
      error: null,
    });
    authMocks.onAuthStateChange.mockReturnValue({
      data: {
        subscription: {
          unsubscribe: vi.fn(),
        },
      },
    });
  });

  it('redirects when session exists', async () => {
    const wrapper = mount(CallbackPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await flushPromises();

    expect(wrapper.text()).toContain('Finishing sign-in');
    expect(navigateToMock).toHaveBeenCalledWith('/oauth/consent?authorization_id=auth-123');
  });

  it('shows an error when Supabase is not available', async () => {
    state.supabase = null;

    const wrapper = mount(CallbackPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await flushPromises();

    expect(wrapper.text()).toContain('Supabase client is not available.');
  });

  it('shows an error when session lookup fails', async () => {
    authMocks.getSession.mockResolvedValueOnce({
      data: { session: null },
      error: { message: 'bad session' },
    });

    const wrapper = mount(CallbackPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await flushPromises();

    expect(wrapper.text()).toContain('bad session');
  });

  it('defaults to the root path when returnTo is missing', async () => {
    state.route = { query: {} };

    mount(CallbackPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await flushPromises();

    expect(navigateToMock).toHaveBeenCalledWith('/');
  });

  it('waits for auth state when session is missing', async () => {
    const unsubscribe = vi.fn();
    // eslint-disable-next-line no-unused-vars
    type AuthHandler = (...args: unknown[]) => void;
    let handler: AuthHandler | null = null;

    authMocks.getSession.mockResolvedValueOnce({
      data: { session: null },
      error: null,
    });
    authMocks.onAuthStateChange.mockImplementationOnce((callback) => {
      handler = callback;
      return {
        data: {
          subscription: {
            unsubscribe,
          },
        },
      };
    });

    const wrapper = mount(CallbackPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await flushPromises();
    expect(wrapper.text()).toContain('Waiting for authentication to complete');

    handler?.('SIGNED_IN', { access_token: 'token-123' });
    await flushPromises();

    expect(unsubscribe).toHaveBeenCalled();
    expect(navigateToMock).toHaveBeenCalledWith('/oauth/consent?authorization_id=auth-123');
  });

  it('ignores auth events without a session', async () => {
    const unsubscribe = vi.fn();
    // eslint-disable-next-line no-unused-vars
    type AuthHandler = (...args: unknown[]) => void;
    let handler: AuthHandler | null = null;

    authMocks.getSession.mockResolvedValueOnce({
      data: { session: null },
      error: null,
    });
    authMocks.onAuthStateChange.mockImplementationOnce((callback) => {
      handler = callback;
      return {
        data: {
          subscription: {
            unsubscribe,
          },
        },
      };
    });

    mount(CallbackPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await flushPromises();
    handler?.('TOKEN_REFRESHED', null);
    await flushPromises();

    expect(unsubscribe).not.toHaveBeenCalled();
    expect(navigateToMock).not.toHaveBeenCalled();
  });

  it('shows a timeout error when the session never arrives', async () => {
    vi.useFakeTimers();
    const unsubscribe = vi.fn();

    authMocks.getSession.mockResolvedValueOnce({
      data: { session: null },
      error: null,
    });
    authMocks.onAuthStateChange.mockReturnValueOnce({
      data: {
        subscription: {
          unsubscribe,
        },
      },
    });

    const wrapper = mount(CallbackPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await flushPromises();
    expect(wrapper.text()).toContain('Waiting for authentication to complete');

    vi.advanceTimersByTime(6000);
    await flushPromises();

    expect(wrapper.text()).toContain('Session not found. Try signing in again.');
    expect(unsubscribe).toHaveBeenCalled();
    vi.useRealTimers();
  });

  it('preserves an existing error when the timeout fires', async () => {
    vi.useFakeTimers();
    const unsubscribe = vi.fn();

    authMocks.getSession.mockResolvedValueOnce({
      data: { session: null },
      error: null,
    });
    authMocks.onAuthStateChange.mockReturnValueOnce({
      data: {
        subscription: {
          unsubscribe,
        },
      },
    });

    const wrapper = mount(CallbackPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    await flushPromises();
    (wrapper.vm as { error: string }).error = 'Already failed';

    vi.advanceTimersByTime(6000);
    await flushPromises();

    expect(wrapper.text()).toContain('Already failed');
    expect(unsubscribe).not.toHaveBeenCalled();
    vi.useRealTimers();
  });
});
