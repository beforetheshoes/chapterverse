import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';

import App from '../../app/app.vue';

describe('app shell', () => {
  it('renders the heading and core content', () => {
    const wrapper = mount(App, {
      global: {
        stubs: {
          NuxtRouteAnnouncer: { template: '<div data-test="announcer" />' },
          NuxtWelcome: { template: '<div data-test="welcome" />' },
        },
      },
    });

    expect(wrapper.get('[data-test="app-title"]').text()).toBe('ChapterVerse');
    expect(wrapper.get('[data-test="announcer"]').exists()).toBe(true);
    expect(wrapper.get('[data-test="welcome"]').exists()).toBe(true);
  });
});
