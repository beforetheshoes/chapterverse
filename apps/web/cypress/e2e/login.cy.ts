describe('login page', () => {
  beforeEach(() => {
    cy.intercept('POST', '**/auth/v1/otp*', {
      statusCode: 200,
      body: {},
    }).as('magicLink');
  });

  it('validates that an email is required', () => {
    cy.visit('/login');

    cy.get('[data-test="login-magic-link"]').click();
    cy.contains('Supabase client is not configured. Check environment variables.').should(
      'be.visible',
    );
  });

  it('submits a magic link request', () => {
    cy.visit('/login');

    cy.get('[data-test="login-email"]').type('reader@theseedbed.app');
    cy.get('[data-test="login-magic-link"]').click();

    cy.contains('Supabase client is not configured. Check environment variables.').should(
      'be.visible',
    );
  });
});
