import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ThemeProvider, useTheme } from "../app/providers/ThemeProvider";
function Probe() {
  const { theme } = useTheme();
  return (
    <>
      <span>{theme}</span>
      <button onClick={() => useTheme}>noop</button>
    </>
  );
}
function Switch() {
  const { theme, setTheme } = useTheme();
  return <button onClick={() => setTheme("light")}>{theme}</button>;
}
describe("theme preference", () => {
  it("defaults to light on first visit", () => {
    render(
      <ThemeProvider>
        <Probe />
      </ThemeProvider>,
    );
    expect(screen.getByText("light")).toBeInTheDocument();
    expect(document.documentElement).not.toHaveClass("dark");
  });
  it("switches theme and persists it", async () => {
    render(
      <ThemeProvider>
        <Switch />
      </ThemeProvider>,
    );
    await userEvent.click(screen.getByRole("button"));
    expect(screen.getByText("light")).toBeInTheDocument();
    expect(localStorage.getItem("swift-theme")).toBe("light");
    expect(document.documentElement).not.toHaveClass("dark");
  });
});
