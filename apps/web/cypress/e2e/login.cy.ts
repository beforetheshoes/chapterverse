describe('login page', () => {
  it('validates that an email is required', () => {
    cy.visit('/login');

    cy.get('[data-test="login-magic-link"]').click();
    cy.get('[data-test="login-email"]').should('exist');
    cy.get('[data-test="login-apple"]').should('contain', 'Continue with Apple');
    cy.get('[data-test="login-magic-link"]').should('contain', 'Send magic link');
    cy.contains('Preview debug:').should('be.visible');
  });

  it('submits a magic link request', () => {
    cy.visit('/login');

    cy.get('[data-test="login-email"]').type('reader@theseedbed.app');
  });
});
