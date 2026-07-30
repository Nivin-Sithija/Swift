import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Tabs } from "../../components/ui/Tabs";

const items = [
  { value: "conversation", label: "Conversation" },
  { value: "evidence", label: "Evidence" },
];

describe("Tabs", () => {
  it("selects the first item by default", () => {
    render(<Tabs items={items} />);
    expect(screen.getByRole("tab", { name: "Conversation" })).toHaveAttribute("aria-selected", "true");
  });

  it("switches active tab on click and calls onChange", async () => {
    const onChange = vi.fn();
    render(<Tabs items={items} onChange={onChange} />);
    await userEvent.click(screen.getByRole("tab", { name: "Evidence" }));
    expect(screen.getByRole("tab", { name: "Evidence" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tab", { name: "Conversation" })).toHaveAttribute("aria-selected", "false");
    expect(onChange).toHaveBeenCalledWith("evidence");
  });
});
