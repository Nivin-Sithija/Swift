import { describe, expect, it, vi, afterEach } from "vitest";
import { isTicketSort, sortTickets, urgencyScore } from "../lib/utils";
import { restTicketService } from "../services/restTicketService";
import type { Ticket } from "../types";

const now = Date.parse("2026-10-02T12:00:00Z");
const ticket = (id: string, intrinsicSeverity: number, waitingMinutes = 0, slaMinutes = 480) => ({
  id, createdAt: new Date(now - waitingMinutes * 60_000).toISOString(),
  urgency: { intrinsicSeverity, waitingMinutes, slaMinutes, agingAlpha: 16,
    evaluatedAt: new Date(now).toISOString(), active: true, score: 0, mode: "log_pool" },
} as Ticket);

afterEach(() => vi.unstubAllGlobals());

describe("dynamic queue urgency", () => {
  it("allows an old low ticket to overtake a fresh medium and advances without refetching", () => {
    const low = ticket("old", 0.01, 2880);
    const medium = ticket("fresh", 0.4, 0, 120);
    expect(sortTickets([medium, low], "urgency", now).map(t => t.id)).toEqual(["old", "fresh"]);
    expect(urgencyScore(low, now + 60_000)).toBeGreaterThan(urgencyScore(low, now));
  });
  it("puts completed tickets last and deterministically breaks ties", () => {
    const a = ticket("A", 0.4), b = ticket("B", 0.4), closed = ticket("closed", 1, 10000);
    closed.urgency!.active = false;
    expect(sortTickets([closed, b, a], "urgency", now).map(t => t.id)).toEqual(["A", "B", "closed"]);
  });
  it("rejects invalid URL sorts", () => {
    expect(isTicketSort("urgency")).toBe(true);
    expect(isTicketSort("invalid")).toBe(false);
  });
  it("loads beyond the first 100 tickets and maps urgency data", async () => {
    const prediction = { value: "medium", confidence: 0.8, model_version: "test", predicted_at: new Date(now).toISOString() };
    const item = (index: number) => ({ id: `SW-${index}`, category: prediction, priority: prediction,
      sentiment: prediction, attachments: [], responses: [], events: [], notes: [],
      urgency: { score: 2, intrinsic_severity: 0.4, sla_minutes: 120, waiting_minutes: 30,
        aging_alpha: 16, evaluated_at: new Date(now).toISOString(), active: true, mode: "log_pool" } });
    const fetcher = vi.fn()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ items: Array.from({ length: 100 }, (_, i) => item(i)), total: 101 }) })
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ items: [item(100)], total: 101 }) });
    vi.stubGlobal("fetch", fetcher);
    const loaded = await restTicketService.getTickets();
    expect(loaded).toHaveLength(101);
    expect(loaded[100].id).toBe("SW-100");
    expect(loaded[100].urgency?.intrinsicSeverity).toBe(0.4);
    expect(fetcher.mock.calls[1][0]).toContain("page=2");
  });
});
