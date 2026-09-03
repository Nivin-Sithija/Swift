import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { AuthProvider } from "../app/providers/AuthProvider";
import { ThemeProvider } from "../app/providers/ThemeProvider";
import { LanguageProvider } from "../app/providers/LanguageProvider";
import { AppRoutes } from "../app/router/Routes";
const renderApp = (route: string) =>
  render(
    <ThemeProvider>
      <LanguageProvider>
        <MemoryRouter initialEntries={[route]}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </MemoryRouter>
      </LanguageProvider>
    </ThemeProvider>,
  );
describe("authentication and role routes", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  it("shows validation for incomplete login", async () => {
    renderApp("/login");
    await userEvent.click(
      screen.getByRole("button", { name: /sign in securely/i }),
    );
    expect(await screen.findByText(/valid email/i)).toBeInTheDocument();
    expect(screen.getByText(/at least 8/i)).toBeInTheDocument();
  });
  it("keeps staff login at its URL-only endpoint", () => {
    const publicLogin = renderApp("/login");
    expect(screen.queryByRole("tab", { name: /support agent/i })).not.toBeInTheDocument();
    expect(screen.queryByText(/staff sign in/i)).not.toBeInTheDocument();
    publicLogin.unmount();

    renderApp("/admin/login");
    expect(screen.getByRole("heading", { name: /staff sign in/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /support agent/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /administrator/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /create an account/i })).toHaveAttribute(
      "href",
      "/register?role=agent",
    );
  });

  it("returns agent registration to the staff login", () => {
    renderApp("/register?role=agent");
    expect(screen.getByRole("link", { name: /sign in/i })).toHaveAttribute(
      "href",
      "/admin/login",
    );
  });
  it("redirects unauthenticated protected routes", () => {
    renderApp("/agent/dashboard");
    expect(
      screen.getByRole("heading", { name: /staff sign in/i }),
    ).toBeInTheDocument();
  });
});
