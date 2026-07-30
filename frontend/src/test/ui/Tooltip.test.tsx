import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Tooltip } from "../../components/ui/Tooltip";

describe("Tooltip", () => {
  it("is hidden until hovered", async () => {
    render(
      <Tooltip label="Manual review required">
        <button>Confidence</button>
      </Tooltip>,
    );
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
    await userEvent.hover(screen.getByRole("button"));
    expect(screen.getByRole("tooltip")).toHaveTextContent("Manual review required");
    await userEvent.unhover(screen.getByRole("button"));
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });
});
