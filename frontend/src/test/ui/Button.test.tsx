import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Button, IconButton } from "../../components/ui/Button";
import { Search } from "lucide-react";

describe("Button", () => {
  it("renders children and fires onClick", async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Approve Reply</Button>);
    await userEvent.click(screen.getByRole("button", { name: "Approve Reply" }));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("does not fire onClick when disabled", async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick} disabled>Approve Reply</Button>);
    await userEvent.click(screen.getByRole("button", { name: "Approve Reply" }));
    expect(onClick).not.toHaveBeenCalled();
  });

  it("iconOnly hides children and still needs an accessible name from the caller", () => {
    render(<Button icon={Search} iconOnly aria-label="Search" />);
    expect(screen.getByRole("button", { name: "Search" })).toBeInTheDocument();
    expect(screen.queryByText("Search")).not.toBeInTheDocument();
  });
});

describe("IconButton", () => {
  it("renders as a secondary-styled button when active", () => {
    render(<IconButton icon={Search} active aria-label="Search" />);
    expect(screen.getByRole("button", { name: "Search" })).toHaveClass("bg-surface-card");
  });
});
