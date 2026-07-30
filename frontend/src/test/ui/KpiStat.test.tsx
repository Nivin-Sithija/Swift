import { render, screen } from "@testing-library/react";
import { KpiStat } from "../../components/ui/KpiStat";

describe("KpiStat", () => {
  it("renders label and value without a delta row", () => {
    render(<KpiStat label="Open Tickets" value={128} />);
    expect(screen.getByText("Open Tickets")).toBeInTheDocument();
    expect(screen.getByText("128")).toBeInTheDocument();
  });

  it("renders the delta and sublabel with the requested tone", () => {
    render(
      <KpiStat
        label="Avg. Response Time"
        value="4m 12s"
        delta="↓ 8%"
        deltaTone="success"
        sublabel="vs last week"
      />,
    );
    expect(screen.getByText("↓ 8%")).toHaveClass("text-success-text");
    expect(screen.getByText("vs last week")).toBeInTheDocument();
  });
});
