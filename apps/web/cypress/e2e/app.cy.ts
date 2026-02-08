describe('home page', () => {
  it('renders the app title', () => {
    cy.visit('/');
    cy.get('[data-test="hero-title"]').should('contain', 'The Seedbed');
    cy.get('[data-test="primary-cta"]').should('contain', 'Explore library');
    cy.get('[data-test="primary-cta"]').should('have.attr', 'href', '/library');
    cy.get('[data-test="hero-email-input"]').should('exist');
  });

  it('renders search and library pages', () => {
    cy.visit('/books/search');
    cy.get('[data-test="search-card"]', { timeout: 15000 }).should(
      'contain',
      'Search and import books',
    );

    cy.visit('/library');
    cy.get('[data-test="library-card"]', { timeout: 15000 }).should('contain', 'Your library');
  });
});
