import { mount } from '@vue/test-utils';
import PrimeVue from 'primevue/config';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const state = vi.hoisted(() => ({
  route: { fullPath: '/books/search' },
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

import SearchPage from '../../../app/pages/books/search.vue';

const mountPage = () =>
  mount(SearchPage, {
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

describe('books search page', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    apiRequest.mockReset();
    state.route = { fullPath: '/books/search' };
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('shows minimum length hint for short queries', async () => {
    const wrapper = mountPage();
    await wrapper.get('[data-test="search-input"]').setValue('h');
    await vi.advanceTimersByTimeAsync(350);

    expect(apiRequest).not.toHaveBeenCalled();
    expect(wrapper.get('[data-test="search-hint"]').text()).toContain('at least 2');
  });

  it('searches books with debounce', async () => {
    apiRequest.mockResolvedValueOnce({
      items: [
        {
          work_key: '/works/OL1W',
          title: 'Book A',
          author_names: ['Author A'],
          first_publish_year: 2000,
        },
      ],
    });

    const wrapper = mountPage();

    await wrapper.get('[data-test="search-input"]').setValue('harry');
    await vi.advanceTimersByTimeAsync(350);

    expect(apiRequest).toHaveBeenCalledWith('/api/v1/books/search', {
      query: { query: 'harry', limit: 10, page: 1 },
    });
    expect(wrapper.text()).toContain('Book A');
  });

  it('clears the prior debounce timer when query changes rapidly', async () => {
    apiRequest.mockResolvedValue({ items: [] });
    const wrapper = mountPage();

    await wrapper.get('[data-test="search-input"]').setValue('ha');
    await wrapper.get('[data-test="search-input"]').setValue('har');
    await vi.advanceTimersByTimeAsync(350);

    expect(apiRequest).toHaveBeenCalledTimes(1);
  });

  it('shows empty-state hint when no results are found', async () => {
    apiRequest.mockResolvedValueOnce({ items: [] });
    const wrapper = mountPage();

    await wrapper.get('[data-test="search-input"]').setValue('unknown');
    await vi.advanceTimersByTimeAsync(350);

    expect(wrapper.get('[data-test="search-hint"]').text()).toContain('No books found');
  });

  it('renders unknown author fallback and no first-publish label when missing', async () => {
    apiRequest.mockResolvedValueOnce({
      items: [
        {
          work_key: '/works/OL1W',
          title: 'Book A',
          author_names: [],
          first_publish_year: null,
        },
      ],
    });

    const wrapper = mountPage();

    await wrapper.get('[data-test="search-input"]').setValue('harry');
    await vi.advanceTimersByTimeAsync(350);

    expect(wrapper.text()).toContain('Unknown author');
    expect(wrapper.text()).not.toContain('First published:');
  });

  it('shows api client errors from search calls', async () => {
    apiRequest.mockRejectedValueOnce(new ApiClientErrorMock('Auth required', 'auth_required', 401));
    const wrapper = mountPage();

    await wrapper.get('[data-test="search-input"]').setValue('harry');
    await vi.advanceTimersByTimeAsync(350);

    expect(wrapper.get('[data-test="search-error"]').text()).toContain('Auth required');
    const loginLink = wrapper.get('[data-test="search-login-link"]');
    expect(loginLink.attributes('href')).toBe('/login?returnTo=%2Fbooks%2Fsearch');
  });

  it('shows generic errors from search calls', async () => {
    apiRequest.mockRejectedValueOnce(new Error('boom'));
    const wrapper = mountPage();

    await wrapper.get('[data-test="search-input"]').setValue('harry');
    await vi.advanceTimersByTimeAsync(350);

    expect(wrapper.get('[data-test="search-error"]').text()).toContain('Unable to search');
  });

  it('imports and adds a searched book', async () => {
    apiRequest
      .mockResolvedValueOnce({
        items: [
          {
            work_key: '/works/OL1W',
            title: 'Book A',
            author_names: ['Author A'],
            first_publish_year: 2000,
          },
        ],
      })
      .mockResolvedValueOnce({ work: { id: 'work-1' } })
      .mockResolvedValueOnce({ created: true });

    const wrapper = mountPage();

    await wrapper.get('[data-test="search-input"]').setValue('harry');
    await vi.advanceTimersByTimeAsync(350);
    await wrapper.get('[data-test="search-add-0"]').trigger('click');

    expect(apiRequest).toHaveBeenNthCalledWith(2, '/api/v1/books/import', {
      method: 'POST',
      body: { work_key: '/works/OL1W' },
    });
    expect(apiRequest).toHaveBeenNthCalledWith(3, '/api/v1/library/items', {
      method: 'POST',
      body: { work_id: 'work-1', status: 'to_read' },
    });
    expect(wrapper.get('[data-test="search-message"]').text()).toContain('added');
  });

  it('uses the currently selected status when adding to library', async () => {
    apiRequest
      .mockResolvedValueOnce({
        items: [
          {
            work_key: '/works/OL1W',
            title: 'Book A',
            author_names: ['Author A'],
            first_publish_year: 2000,
          },
        ],
      })
      .mockResolvedValueOnce({ work: { id: 'work-1' } })
      .mockResolvedValueOnce({ created: true });

    const wrapper = mountPage();

    await wrapper.get('[data-test="status-select"]').trigger('click');
    await wrapper.get('[data-test="search-input"]').setValue('harry');
    await vi.advanceTimersByTimeAsync(350);
    await wrapper.get('[data-test="search-add-0"]').trigger('click');

    expect(apiRequest).toHaveBeenNthCalledWith(3, '/api/v1/library/items', {
      method: 'POST',
      body: { work_id: 'work-1', status: 'reading' },
    });
  });

  it('shows duplicate message when already in library', async () => {
    apiRequest
      .mockResolvedValueOnce({
        items: [
          {
            work_key: '/works/OL1W',
            title: 'Book A',
            author_names: ['Author A'],
            first_publish_year: 2000,
          },
        ],
      })
      .mockResolvedValueOnce({ work: { id: 'work-1' } })
      .mockResolvedValueOnce({ created: false });

    const wrapper = mountPage();

    await wrapper.get('[data-test="search-input"]').setValue('harry');
    await vi.advanceTimersByTimeAsync(350);
    await wrapper.get('[data-test="search-add-0"]').trigger('click');

    expect(wrapper.get('[data-test="search-message"]').text()).toContain('already in your library');
  });

  it('shows api client errors from import flow', async () => {
    apiRequest
      .mockResolvedValueOnce({
        items: [
          {
            work_key: '/works/OL1W',
            title: 'Book A',
            author_names: ['Author A'],
            first_publish_year: 2000,
          },
        ],
      })
      .mockRejectedValueOnce(new ApiClientErrorMock('Import denied', 'denied', 403));

    const wrapper = mountPage();

    await wrapper.get('[data-test="search-input"]').setValue('harry');
    await vi.advanceTimersByTimeAsync(350);
    await wrapper.get('[data-test="search-add-0"]').trigger('click');

    expect(wrapper.get('[data-test="search-error"]').text()).toContain('Import denied');
  });

  it('shows generic errors from import flow', async () => {
    apiRequest
      .mockResolvedValueOnce({
        items: [
          {
            work_key: '/works/OL1W',
            title: 'Book A',
            author_names: ['Author A'],
            first_publish_year: 2000,
          },
        ],
      })
      .mockRejectedValueOnce(new Error('boom'));

    const wrapper = mountPage();

    await wrapper.get('[data-test="search-input"]').setValue('harry');
    await vi.advanceTimersByTimeAsync(350);
    await wrapper.get('[data-test="search-add-0"]').trigger('click');

    expect(wrapper.get('[data-test="search-error"]').text()).toContain('Unable to import');
  });

  it('clears pending timer on unmount', async () => {
    const clearSpy = vi.spyOn(globalThis, 'clearTimeout');
    const wrapper = mountPage();
    await wrapper.get('[data-test="search-input"]').setValue('harry');
    wrapper.unmount();

    expect(clearSpy).toHaveBeenCalled();
    clearSpy.mockRestore();
  });

  it('unmounts without a pending timer', () => {
    const wrapper = mountPage();
    expect(() => wrapper.unmount()).not.toThrow();
  });
});
