import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { TopNav } from "../../components/ui/TopNav";

const items = [
  { to: "/agent/dashboard", label: "Dashboard" },
  { to: "/agent/tickets", label: "Tickets" },
];

describe("TopNav", () => {
  it("renders the logo, nav items and right slot", () => {
    render(
      <MemoryRouter initialEntries={["/agent/dashboard"]}>
        <TopNav
          logo={<span>Swift</span>}
          items={items}
          right={<button>Sign out</button>}
        />
      </MemoryRouter>,
    );
    expect(screen.getByText("Swift")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Dashboard" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Sign out" }),
    ).toBeInTheDocument();
  });

  it("marks the current route's link active", () => {
    render(
      <MemoryRouter initialEntries={["/agent/tickets"]}>
        <TopNav logo={<span>Swift</span>} items={items} />
      </MemoryRouter>,
    );
    expect(screen.getByRole("link", { name: "Tickets" })).toHaveClass(
      "text-primary-text",
    );
    expect(screen.getByRole("link", { name: "Dashboard" })).toHaveClass(
      "text-text-secondary",
    );
  });
});
