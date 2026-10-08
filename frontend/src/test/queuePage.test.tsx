import { act, cleanup, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";
import { AgentQueuePage } from "../pages/agent/AgentQueuePage";
import { ticketService } from "../services/serviceSelector";
import type { Ticket } from "../types";

vi.mock("../app/providers/AuthProvider", () => ({
  useAuth: () => ({ user: { id: "agent", name: "Agent" } }),
}));
vi.mock("../app/providers/LanguageProvider", () => ({
  useLanguage: () => ({ tr: (s: string) => s }),
}));
vi.mock("../services/serviceSelector", () => ({
  ticketService: { getTickets: vi.fn() },
}));

afterEach(() => { cleanup(); vi.useRealTimers(); });

it("defaults to dynamic urgency and updates visible order after 30 seconds", async () => {
  vi.useFakeTimers();
  const now = Date.parse("2026-10-02T12:00:00Z");
  vi.setSystemTime(now);
  const makeTicket = (id: string, severity: number, wait: number, sla: number) => ({
    id, customerName: "Customer", customerId: "customer", subject: "Queue test", message: "Help",
    createdAt: new Date(now - wait * 60_000).toISOString(), updatedAt: new Date(now).toISOString(),
    priority: { value: "low" }, category: { value: "card_arrival", confidence: 90 },
    sentiment: { value: "neutral" }, language: "english", status: "in_review",
    urgency: { active: true, intrinsicSeverity: severity, waitingMinutes: wait, slaMinutes: sla,
      evaluatedAt: new Date(now).toISOString(), agingAlpha: 16, mode: "label_fallback" },
  } as Ticket);
  vi.mocked(ticketService.getTickets).mockResolvedValue([
    makeTicket("SW-FRESH", 0.4, 0, 120), makeTicket("SW-OLD", 0.01, 1185, 480),
  ]);
  await act(async () => {
    render(<MemoryRouter><AgentQueuePage /></MemoryRouter>);
  });
  expect(screen.getByRole("combobox", { name: "Sort tickets" })).toHaveValue("urgency");
  expect(within(screen.getAllByRole("row")[1]).getByText("SW-OLD")).toBeInTheDocument();
  expect(within(screen.getAllByRole("row")[1]).getByText(/Urgency .*estimated/)).toBeInTheDocument();
  await act(async () => { vi.advanceTimersByTime(30_000); });
  expect(within(screen.getAllByRole("row")[1]).getByText("SW-FRESH")).toBeInTheDocument();
  expect(ticketService.getTickets).toHaveBeenCalledTimes(1);
});
