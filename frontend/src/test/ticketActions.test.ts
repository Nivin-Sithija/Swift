import { restTicketService } from "../services/restTicketService";
import { canAssignTicket, canChangeTicketStatus } from "../lib/ticketActions";
import { vi, describe, it, expect, afterEach } from "vitest";

const prediction = {
  id: "prediction",
  value: "low",
  confidence: 0.9,
  model_version: "test",
  predicted_at: "2026-09-27",
};
const ticket = {
  id: "SW-1",
  category: prediction,
  priority: prediction,
  sentiment: prediction,
  responses: [],
  attachments: [],
  events: [],
  notes: [],
  status: "assigned",
  assigned_agent: "Agent",
};
afterEach(() => vi.unstubAllGlobals());

describe("ticket actions", () => {
  it("keeps finished tickets from being assigned, escalated, or resolved again", () => {
    for (const status of ["resolved", "closed"] as const) {
      expect(canAssignTicket(status)).toBe(false);
      expect(canChangeTicketStatus(status, "resolved")).toBe(false);
      expect(canChangeTicketStatus(status, "escalated")).toBe(false);
    }
    expect(canChangeTicketStatus("resolved", "closed")).toBe(true);
    expect(canChangeTicketStatus("closed", "closed")).toBe(false);
  });
  it("saves the assignee when assignment and status are supplied together", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(ticket)));
    vi.stubGlobal(
      "fetch",
      fetchMock.mockImplementation(
        async () => new Response(JSON.stringify(ticket)),
      ),
    );
    await restTicketService.updateTicket("SW-1", {
      assignedAgent: "Agent",
      status: "assigned",
    });
    expect(fetchMock.mock.calls[0][0]).toContain("/tickets/SW-1/assignment");
    expect(
      fetchMock.mock.calls.some((call) => String(call[0]).endsWith("/status")),
    ).toBe(false);
  });
  it("uses the escalation endpoint so queue and audit effects are applied", async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify(ticket)));
    vi.stubGlobal("fetch", fetchMock);
    await restTicketService.updateTicket("SW-1", { status: "escalated" });
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/escalate"),
      expect.objectContaining({ method: "POST" }),
    );
  });
  it("propagates server failures instead of reporting success", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(JSON.stringify({ detail: "Cannot assign" }), {
            status: 409,
          }),
      ),
    );
    await expect(
      restTicketService.updateTicket("SW-1", { assignedAgent: "Agent" }),
    ).rejects.toThrow("Cannot assign");
  });
});
