describe('home page', () => {
  it('renders the app title', () => {
    cy.visit('/');
    cy.get('[data-test="app-title"]').should('contain', 'ChapterVerse');
  });
});
