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
    await waitFor(
      () => expect(screen.getByText("Assigned to me")).toBeInTheDocument(),
      { timeout: 3000 },
    );
    expect(screen.getByText("Avg. first response")).toBeInTheDocument();
  });

  it("creates a customer account and opens the customer portal", async () => {
    const registration = renderApp("/register");
    await userEvent.type(screen.getByLabelText(/full name/i), "Nimal Perera");
    await userEvent.type(screen.getByLabelText(/email address/i), "nimal@example.com");
    await userEvent.type(screen.getByLabelText(/^password$/i), "securepass123");
    await userEvent.type(screen.getByLabelText(/confirm password/i), "securepass123");
    await userEvent.click(screen.getByRole("button", { name: /^create account$/i }));
    expect(await screen.findByRole("heading", { name: /how can we help/i })).toBeInTheDocument();
    expect(JSON.parse(localStorage.getItem("swift-mock-accounts") || "[]")).toHaveLength(1);

    registration.unmount();
    sessionStorage.clear();
    renderApp("/login");
    await userEvent.type(screen.getByLabelText(/email address/i), "nimal@example.com");
    await userEvent.type(screen.getByPlaceholderText(/enter your password/i), "securepass123");
    await userEvent.click(screen.getByRole("button", { name: /sign in securely/i }));
    expect(await screen.findByRole("heading", { name: /how can we help/i })).toBeInTheDocument();
  });

  it("requires the demo registration code before opening the agent portal", async () => {
    renderApp("/register?role=agent");
    expect(screen.getByRole("tab", { name: /support agent/i })).toHaveAttribute("aria-selected", "true");
    await userEvent.type(screen.getByLabelText(/full name/i), "Amara Agent");
    await userEvent.type(screen.getByLabelText(/email address/i), "amara@example.com");
    await userEvent.type(screen.getByLabelText(/^password$/i), "securepass123");
    await userEvent.type(screen.getByLabelText(/confirm password/i), "securepass123");
    await userEvent.type(screen.getByLabelText(/registration code/i), "wrong-code");
    await userEvent.click(screen.getByRole("button", { name: /^create account$/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/invalid support-agent registration code/i);
  });
});
