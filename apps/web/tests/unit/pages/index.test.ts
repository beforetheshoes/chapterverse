import { mount } from '@vue/test-utils';
import PrimeVue from 'primevue/config';
import { describe, expect, it } from 'vitest';

import IndexPage from '../../../app/pages/index.vue';

describe('index page', () => {
  it('renders key PrimeVue content', async () => {
    const wrapper = mount(IndexPage, {
      global: {
        plugins: [[PrimeVue, { ripple: false }]],
      },
    });

    expect(wrapper.get('[data-test="hero-title"]').text()).toBe('The Seedbed');
    expect(wrapper.get('[data-test="hero-subtitle"]').text()).toContain('reading history');
    const emailInput = wrapper.get('[data-test="hero-email-input"]');
    await emailInput.setValue('reader@theseedbed.app');
    expect((emailInput.element as HTMLInputElement).value).toBe('reader@theseedbed.app');
    expect(wrapper.get('[data-test="primary-cta"]').text()).toContain('Explore library');
    expect(wrapper.get('[data-test="secondary-cta"]').text()).toContain('Add a book');
    expect(wrapper.get('[data-test="status-card"]').exists()).toBe(true);
  });
});
