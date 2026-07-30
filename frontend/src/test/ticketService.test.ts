import { mockTicketService } from "../services/ticketService";
import { mockTickets } from "../mocks/tickets";

describe("mock ticket service", () => {
  it("rejects an unknown ticket id instead of resolving empty", async () => {
    await expect(mockTicketService.getTicket("SW-0000-0000")).rejects.toThrow(
      /not found/i,
    );
  });
  it("returns queue neighbours for the detail page navigation", async () => {
    const [first, second, third] = mockTickets;
    await expect(
      mockTicketService.getAdjacentTicketIds(second.id),
    ).resolves.toEqual({ previous: first.id, next: third.id });
  });
  it("has no previous before the first ticket and no next after the last", async () => {
    const last = mockTickets[mockTickets.length - 1];
    await expect(
      mockTicketService.getAdjacentTicketIds(mockTickets[0].id),
    ).resolves.toMatchObject({ previous: undefined });
    await expect(
      mockTicketService.getAdjacentTicketIds(last.id),
    ).resolves.toMatchObject({ next: undefined });
  });
  it("returns no neighbours for an unknown id rather than throwing", async () => {
    await expect(
      mockTicketService.getAdjacentTicketIds("SW-0000-0000"),
    ).resolves.toEqual({});
  });
  it("stores the note it returns so the UI and service agree on its id", async () => {
    const note = await mockTicketService.addInternalNote(
      mockTickets[0].id,
      "Verified the reference number.",
    );
    const ticket = await mockTicketService.getTicket(mockTickets[0].id);
    expect(ticket.notes.map((n) => n.id)).toContain(note.id);
  });
});
