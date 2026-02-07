describe('home page', () => {
  it('renders the app title', () => {
    cy.visit('/');
    cy.get('[data-test="hero-title"]').should('contain', 'The Seedbed');
    cy.get('[data-test="primary-cta"]').should('contain', 'Explore library');
    cy.get('[data-test="hero-email-input"]').should('exist');
  });
});
