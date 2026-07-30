import { render, screen } from "@testing-library/react";
import { Card } from "../../components/ui/Card";

describe("Card", () => {
  it("renders children without a title", () => {
    render(<Card>Body content</Card>);
    expect(screen.getByText("Body content")).toBeInTheDocument();
    expect(screen.queryByRole("heading")).not.toBeInTheDocument();
  });

  it("renders a title heading and an action slot", () => {
    render(
      <Card title="Recent Tickets" action={<button>View all</button>}>
        Body
      </Card>,
    );
    expect(
      screen.getByRole("heading", { name: "Recent Tickets" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "View all" }),
    ).toBeInTheDocument();
  });
});
