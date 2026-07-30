import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { MockAuthProvider } from "../app/providers/AuthProvider";
import { ThemeProvider } from "../app/providers/ThemeProvider";
import { LanguageProvider } from "../app/providers/LanguageProvider";
import { AppRoutes } from "../app/router/Routes";
const renderApp = (route: string) =>
  render(
    <ThemeProvider>
      <LanguageProvider>
        <MemoryRouter initialEntries={[route]}>
          <MockAuthProvider>
            <AppRoutes />
          </MockAuthProvider>
        </MemoryRouter>
      </LanguageProvider>
    </ThemeProvider>,
  );
describe("authentication and role routes", () => {
  it("shows validation for incomplete login", async () => {
    renderApp("/login");
    await userEvent.click(
      screen.getByRole("button", { name: /sign in securely/i }),
    );
    expect(await screen.findByText(/valid email/i)).toBeInTheDocument();
    expect(screen.getByText(/at least 8/i)).toBeInTheDocument();
  });
  it("redirects unauthenticated protected routes", () => {
    renderApp("/agent/dashboard");
    expect(
      screen.getByRole("heading", { name: /welcome to swift/i }),
    ).toBeInTheDocument();
  });
  it("prevents customer session from opening agent routes", async () => {
    sessionStorage.setItem(
      "swift-session",
      JSON.stringify({
        id: "c1",
        name: "Maya",
        email: "customer@swift.demo",
        role: "customer",
      }),
    );
    renderApp("/agent/dashboard");
    expect(
      await screen.findByRole("heading", { name: /how can we help/i }),
    ).toBeInTheDocument();
  });
  it("renders agent dashboard metrics for an agent", async () => {
    sessionStorage.setItem(
      "swift-session",
      JSON.stringify({
        id: "a1",
        name: "Anika Fernando",
        email: "agent@swift.demo",
        role: "agent",
      }),
    );
    renderApp("/agent/dashboard");
    await waitFor(() =>
      expect(screen.getByText("Assigned to me")).toBeInTheDocument(),
    );
    expect(screen.getByText("Avg. first response")).toBeInTheDocument();
  });
});
