import { render, screen, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AgentTicketDetailPage } from "../pages/agent/AgentTicketDetailPage";
import { ticketService } from "../services/serviceSelector";
import type { Ticket } from "../types";
vi.mock("../app/providers/AuthProvider", () => ({
  useAuth: () => ({ user: { id: "a1", name: "Agent" } }),
}));
vi.mock("../app/providers/LanguageProvider", () => ({
  useLanguage: () => ({ tr: (s: string) => s }),
}));
vi.mock("../services/serviceSelector", () => ({
  ticketService: {
    getTicket: vi.fn(),
    getAdjacentTicketIds: vi.fn(),
    updateTicket: vi.fn(),
    undoEscalation: vi.fn(),
    undoResolution: vi.fn(),
  },
}));
vi.mock("../components/agent/AgentPanels", () => ({
  ImageEvidencePanel: () => null,
  InternalNotes: () => null,
  ResponseEditor: () => null,
  PredictionCard: () => null,
}));
const ticket = {
  id: "SW-1",
  subject: "Help",
  customerName: "Customer",
  createdAt: "2026-09-27",
  status: "assigned",
  assignedAgent: "Agent",
  priority: { value: "high" },
  sentiment: { value: "neutral" },
  language: "english",
  preferredResponseLanguage: "english",
  events: [],
} as unknown as Ticket;
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(ticketService.getAdjacentTicketIds).mockResolvedValue({});
});
afterEach(cleanup);
const show = (value: Ticket) => {
  vi.mocked(ticketService.getTicket).mockResolvedValue(value);
  render(
    <MemoryRouter>
      <AgentTicketDetailPage />
    </MemoryRouter>,
  );
};
describe("ticket command states", () => {
  it("shows completed assignment and updates Resolve after confirmation", async () => {
    show(ticket);
    expect(
      await screen.findByRole("button", { name: "Assigned to me" }),
    ).toBeDisabled();
    vi.mocked(ticketService.updateTicket).mockResolvedValue({
      ...ticket,
      status: "resolved",
    });
    await userEvent.click(screen.getByRole("button", { name: "Resolve" }));
    const buttons = screen.getAllByRole("button", {
      name: "Resolve",
    });
    await userEvent.click(buttons[buttons.length - 1]);
    expect(
      await screen.findByRole("button", { name: "Undo resolution" }),
    ).toBeEnabled();
    expect(screen.getByRole("button", { name: "Close" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Escalate" })).toBeDisabled();
  });
  it("keeps Resolve available and shows an error when saving fails", async () => {
    show(ticket);
    vi.mocked(ticketService.updateTicket).mockRejectedValue(
      new Error("Save failed"),
    );
    await userEvent.click(
      await screen.findByRole("button", { name: "Resolve" }),
    );
    const buttons = screen.getAllByRole("button", {
      name: "Resolve",
    });
    await userEvent.click(buttons[buttons.length - 1]);
    expect(await screen.findByRole("alert")).toHaveTextContent("Save failed");
    expect(
      screen.queryByText("Ticket marked Resolved."),
    ).not.toBeInTheDocument();
  });
});

describe("undo ticket actions", () => {
  it("reopens a resolved ticket after confirmation", async () => {
    show({ ...ticket, status: "resolved" });
    vi.mocked(ticketService.undoResolution).mockResolvedValue({
      ...ticket,
      status: "reopened",
    });
    await userEvent.click(
      await screen.findByRole("button", { name: "Undo resolution" }),
    );
    expect(ticketService.undoResolution).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole("button", { name: "Confirm undo" }));
    expect(
      await screen.findByText("Resolution undone. Ticket reopened."),
    ).toBeInTheDocument();
    expect(ticketService.undoResolution).toHaveBeenCalledWith("SW-1");
    expect(
      screen.queryByRole("button", { name: "Undo resolution" }),
    ).not.toBeInTheDocument();
  });
  it("undoes escalation and restores available actions", async () => {
    show({ ...ticket, status: "escalated" });
    vi.mocked(ticketService.undoEscalation).mockResolvedValue(ticket);
    await userEvent.click(
      await screen.findByRole("button", { name: "Undo escalation" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Confirm undo" }));
    expect(
      await screen.findByText(
        "Escalation undone. Ticket returned to General Support.",
      ),
    ).toBeInTheDocument();
    expect(ticketService.undoEscalation).toHaveBeenCalledWith("SW-1");
    expect(screen.getByRole("button", { name: "Escalate" })).toBeEnabled();
    expect(
      screen.getByRole("button", { name: "Assigned to me" }),
    ).toBeDisabled();
  });
  it("keeps the current state when undo fails and allows retry", async () => {
    show({ ...ticket, status: "escalated" });
    vi.mocked(ticketService.undoEscalation).mockRejectedValue(
      new Error("Could not undo escalation"),
    );
    await userEvent.click(
      await screen.findByRole("button", { name: "Undo escalation" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Confirm undo" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Could not undo escalation",
    );
    expect(screen.getByRole("button", { name: "Confirm undo" })).toBeEnabled();
    expect(
      screen.getByRole("button", { name: "Undo escalation" }),
    ).toBeEnabled();
  });
});
