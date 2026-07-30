import { render, screen } from "@testing-library/react";
import { Avatar } from "../../components/ui/Avatar";

describe("Avatar", () => {
  it("renders up to two initials from the name", () => {
    render(<Avatar name="Nimal Perera" />);
    expect(screen.getByText("NP")).toBeInTheDocument();
  });

  it("renders an image instead of initials when src is given", () => {
    render(<Avatar name="Nimal Perera" src="/avatar.png" />);
    expect(screen.getByRole("img", { name: "Nimal Perera" })).toBeInTheDocument();
    expect(screen.queryByText("NP")).not.toBeInTheDocument();
  });
});
