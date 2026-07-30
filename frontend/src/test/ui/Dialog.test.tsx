import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Dialog } from "../../components/ui/Dialog";

describe("Dialog", () => {
  it("renders nothing when closed", () => {
    render(<Dialog open={false} title="Reject reply" onClose={vi.fn()}>Reason</Dialog>);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("renders title, content and footer when open", () => {
    render(
      <Dialog open title="Reject reply" footer={<button>Confirm</button>} onClose={vi.fn()}>
        Are you sure?
      </Dialog>,
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Are you sure?")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Confirm" })).toBeInTheDocument();
  });

  it("calls onClose when the scrim is clicked but not when the dialog body is clicked", async () => {
    const onClose = vi.fn();
    render(
      <Dialog open title="Reject reply" onClose={onClose}>
        Are you sure?
      </Dialog>,
    );
    await userEvent.click(screen.getByText("Are you sure?"));
    expect(onClose).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole("presentation"));
    expect(onClose).toHaveBeenCalledOnce();
  });
});
