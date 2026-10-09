describe("Swift production frontend", () => {
  for (const viewport of [[1280, 800], [390, 844]]) {
    it(`renders and validates login at ${viewport[0]}x${viewport[1]}`, () => {
      cy.viewport(viewport[0], viewport[1]);
      cy.visit("/login");
      cy.contains("Welcome to Swift").should("be.visible");
      cy.get('input[autocomplete="email"]').type("invalid");
      cy.contains("button", "Sign in securely").click();
      cy.contains("Enter a valid email").should("be.visible");
      cy.get('button[aria-label="dark theme"]').click();
      cy.get("html").should("have.attr", "data-theme", "dark");
    });
  }

  it("renders the registration route and switches account roles", () => {
    cy.visit("/register");
    cy.contains("Create account").should("be.visible");
    cy.contains("Support agent").click();
    cy.contains("Support-agent registration code").should("be.visible");
  });
});
