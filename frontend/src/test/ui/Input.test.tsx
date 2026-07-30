import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createRef } from "react";
import { Search } from "lucide-react";
import { Input } from "../../components/ui/Input";

describe("Input", () => {
  it("accepts typed input", async () => {
    render(<Input aria-label="Search tickets" />);
    const input = screen.getByLabelText("Search tickets");
    await userEvent.type(input, "TCK-1042");
    expect(input).toHaveValue("TCK-1042");
  });

  it("forwards its ref (react-hook-form register compatibility)", () => {
    const ref = createRef<HTMLInputElement>();
    render(<Input ref={ref} aria-label="Email" />);
    expect(ref.current).toBeInstanceOf(HTMLInputElement);
  });

  it("adds left padding when an icon is passed", () => {
    render(<Input icon={Search} aria-label="Search tickets" />);
    expect(screen.getByLabelText("Search tickets")).toHaveClass("pl-8");
  });
});
