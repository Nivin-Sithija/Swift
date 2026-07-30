import { render, screen } from "@testing-library/react";
import { PriorityQueueRow } from "../../components/ui/PriorityQueueRow";

describe("PriorityQueueRow", () => {
  it("renders customer, snippet, category and time", () => {
    render(
      <PriorityQueueRow
        customer="K. Fernando"
        snippet="Card blocked after failed OTP attempts"
        priority="High"
        category="Fraud Report"
        minutesAgo="2m"
      />,
    );
    expect(screen.getByText("K. Fernando")).toBeInTheDocument();
    expect(
      screen.getByText("Card blocked after failed OTP attempts"),
    ).toBeInTheDocument();
    expect(screen.getByText("Fraud Report")).toBeInTheDocument();
    expect(screen.getByText("2m")).toBeInTheDocument();
  });

  it("maps priority to the matching badge tone", () => {
    render(
      <PriorityQueueRow
        customer="A"
        snippet="s"
        priority="High"
        category="c"
        minutesAgo="1m"
      />,
    );
    expect(screen.getByText("High")).toHaveClass("text-error-text");
  });
});
