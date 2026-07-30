import { render, screen } from "@testing-library/react";
import { Badge } from "../../components/ui/Badge";

describe("Badge", () => {
  it("renders label text", () => {
    render(<Badge tone="error">Critical</Badge>);
    expect(screen.getByText("Critical")).toBeInTheDocument();
  });

  it("applies the tone's classes", () => {
    render(<Badge tone="success">Resolved</Badge>);
    expect(screen.getByText("Resolved")).toHaveClass(
      "bg-success-subtle",
      "text-success-text",
    );
  });

  it("defaults to the neutral tone", () => {
    render(<Badge>Web</Badge>);
    expect(screen.getByText("Web")).toHaveClass("bg-neutral-badge-subtle");
  });
});
