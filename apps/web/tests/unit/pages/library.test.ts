import { flushPromises, mount } from '@vue/test-utils';
import PrimeVue from 'primevue/config';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const state = vi.hoisted(() => ({
  route: { fullPath: '/library' },
}));

const apiRequest = vi.hoisted(() => vi.fn());
const ApiClientErrorMock = vi.hoisted(
  () =>
    class ApiClientError extends Error {
      code: string;
      status?: number;

      constructor(message: string, code: string, status?: number) {
        super(message);
        this.code = code;
        this.status = status;
      }
    },
);

vi.mock('~/utils/api', () => ({
  apiRequest,
  ApiClientError: ApiClientErrorMock,
}));

vi.mock('#imports', () => ({
  useRoute: () => state.route,
}));

import LibraryPage from '../../../app/pages/library/index.vue';

const mountPage = () =>
  mount(LibraryPage, {
    global: {
      plugins: [[PrimeVue, { ripple: false }]],
      stubs: {
        NuxtLink: { props: ['to'], template: '<a :href="to"><slot /></a>' },
        Select: {
          props: ['modelValue', 'options'],
          emits: ['update:modelValue'],
          template:
            '<button data-test="select-stub" @click="$emit(`update:modelValue`, `reading`)"></button>',
        },
      },
    },
  });

describe('library page', () => {
  beforeEach(() => {
    apiRequest.mockReset();
    state.route = { fullPath: '/library' };
  });

  it('loads library items on mount', async () => {
    apiRequest.mockResolvedValueOnce({
      items: [
        {
          id: 'item-1',
          work_id: 'work-1',
          work_title: 'Book A',
          status: 'to_read',
          visibility: 'private',
        },
      ],
      next_cursor: null,
    });

    const wrapper = mountPage();

    await flushPromises();

    expect(apiRequest).toHaveBeenCalledWith('/api/v1/library/items', {
      query: { limit: 10, cursor: undefined, status: undefined },
    });
    expect(wrapper.text()).toContain('Book A');
  });

  it('loads next page when load more is clicked', async () => {
    apiRequest
      .mockResolvedValueOnce({
        items: [
          {
            id: 'item-1',
            work_id: 'work-1',
            work_title: 'Book A',
            status: 'to_read',
            visibility: 'private',
          },
        ],
        next_cursor: 'cursor-1',
      })
      .mockResolvedValueOnce({
        items: [
          {
            id: 'item-2',
            work_id: 'work-2',
            work_title: 'Book B',
            status: 'reading',
            visibility: 'private',
          },
        ],
        next_cursor: null,
      });

    const wrapper = mountPage();

    await flushPromises();
    await wrapper.get('[data-test="library-load-more"]').trigger('click');
    await flushPromises();

    expect(apiRequest).toHaveBeenNthCalledWith(2, '/api/v1/library/items', {
      query: { limit: 10, cursor: 'cursor-1', status: undefined },
    });
    expect(wrapper.text()).toContain('Book B');
  });

  it('shows empty state when no items are returned', async () => {
    apiRequest.mockResolvedValueOnce({ items: [], next_cursor: null });

    const wrapper = mountPage();
    await flushPromises();

    expect(wrapper.get('[data-test="library-empty"]').text()).toContain('No library items');
  });

  it('shows api client errors on fetch', async () => {
    apiRequest.mockRejectedValueOnce(
      new ApiClientErrorMock('Sign in required', 'auth_required', 401),
    );

    const wrapper = mountPage();
    await flushPromises();

    expect(wrapper.get('[data-test="library-error"]').text()).toContain('Sign in required');
    const loginLink = wrapper.get('[data-test="library-login-link"]');
    expect(loginLink.attributes('href')).toBe('/login?returnTo=%2Flibrary');
  });

  it('shows generic errors on fetch', async () => {
    apiRequest.mockRejectedValueOnce(new Error('boom'));

    const wrapper = mountPage();
    await flushPromises();

    expect(wrapper.get('[data-test="library-error"]').text()).toContain('Unable to load library');
  });

  it('refetches when status filter changes', async () => {
    apiRequest
      .mockResolvedValueOnce({ items: [], next_cursor: null })
      .mockResolvedValueOnce({ items: [], next_cursor: null });

    const wrapper = mountPage();
    await flushPromises();
    await wrapper.get('[data-test="library-status-filter"]').trigger('click');
    await flushPromises();

    expect(apiRequest).toHaveBeenNthCalledWith(2, '/api/v1/library/items', {
      query: { limit: 10, cursor: undefined, status: 'reading' },
    });
  });

  it('does not request another page when no cursor is present', async () => {
    apiRequest.mockResolvedValueOnce({ items: [], next_cursor: null });

    const wrapper = mountPage();
    await flushPromises();

    expect(wrapper.find('[data-test="library-load-more"]').exists()).toBe(false);
    expect(apiRequest).toHaveBeenCalledTimes(1);
  });
});
