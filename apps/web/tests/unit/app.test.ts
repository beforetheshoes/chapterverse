import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';

import App from '../../app/app.vue';

describe('app shell', () => {
  it('renders the shell and page outlet', () => {
    const wrapper = mount(App, {
      global: {
        stubs: {
          NuxtRouteAnnouncer: { template: '<div data-test="announcer" />' },
          NuxtPage: { template: '<div data-test="page" />' },
        },
      },
    });

    expect(wrapper.get('[data-test="app-shell"]').exists()).toBe(true);
    expect(wrapper.get('[data-test="announcer"]').exists()).toBe(true);
    expect(wrapper.get('[data-test="page"]').exists()).toBe(true);
  });
});
