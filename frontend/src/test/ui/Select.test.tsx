import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Select } from "../../components/ui/Select";

const options = [
  { value: "all", label: "All priorities" },
  { value: "critical", label: "Critical" },
];

describe("Select", () => {
  it("renders a labelled select and reports changes", async () => {
    render(
      <Select
        id="priority"
        label="Priority filter"
        options={options}
        defaultValue="all"
      />,
    );
    const select = screen.getByLabelText("Priority filter");
    await userEvent.selectOptions(select, "critical");
    expect(select).toHaveValue("critical");
  });

  it("renders without a wrapping label when none is given", () => {
    render(
      <Select
        aria-label="Priority filter"
        options={options}
        defaultValue="all"
      />,
    );
    expect(screen.queryByText("Priority filter")).not.toBeInTheDocument();
    expect(screen.getByRole("combobox")).toBeInTheDocument();
  });
});
