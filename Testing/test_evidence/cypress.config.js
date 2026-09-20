const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    baseUrl: "http://127.0.0.1:8080",
    specPattern: "Testing/test_evidence/cypress/e2e/**/*.cy.js",
    supportFile: false,
    video: false,
    screenshotsFolder: "Testing/test_evidence/cypress/screenshots",
  },
});
