import { mockTickets } from "../mocks/tickets";
import type {
  DashboardMetrics,
  InternalNote,
  Ticket,
  User,
  UserRole,
} from "../types";
import { delay } from "../lib/utils";
import { CURRENT_AGENT } from "../lib/constants";

const tickets = structuredClone(mockTickets);

/** Neighbouring ticket ids in queue order, for the detail page's prev/next control. */
export interface AdjacentTickets {
  previous?: string;
  next?: string;
}

export interface TicketService {
  login(email: string, password: string, role: UserRole): Promise<User>;
  logout(): Promise<void>;
  getTickets(): Promise<Ticket[]>;
  getTicket(id: string): Promise<Ticket>;
  getAdjacentTicketIds(id: string): Promise<AdjacentTickets>;
  updateTicket(id: string, patch: Partial<Ticket>): Promise<Ticket>;
  addInternalNote(id: string, text: string): Promise<InternalNote>;
  getDashboardMetrics(): Promise<DashboardMetrics>;
}

export const mockTicketService: TicketService = {
  async login(email, password, role) {
    await delay(500);
    const expected =
      role === "agent" ? "agent@swift.demo" : "customer@swift.demo";
    if (email !== expected || password !== "password123")
      throw new Error("Invalid email or password");
    return role === "agent"
      ? { id: "agent-1", name: CURRENT_AGENT, email, role }
      : { id: "customer-1", name: "Maya Silva", email, role };
  },
  async logout() {
    await delay(100);
  },
  async getTickets() {
    await delay();
    return structuredClone(tickets);
  },
  async getTicket(id) {
    await delay(250);
    const ticket = tickets.find((item) => item.id === id);
    if (!ticket) throw new Error("Ticket not found");
    return structuredClone(ticket);
  },
  async getAdjacentTicketIds(id) {
    const index = tickets.findIndex((item) => item.id === id);
    if (index < 0) return {};
    return {
      previous: tickets[index - 1]?.id,
      next: tickets[index + 1]?.id,
    };
  },
  async updateTicket(id, patch) {
    await delay(250);
    const index = tickets.findIndex((item) => item.id === id);
    if (index < 0) throw new Error("Ticket not found");
    tickets[index] = {
      ...tickets[index],
      ...patch,
      updatedAt: new Date().toISOString(),
    };
    return structuredClone(tickets[index]);
  },
  async addInternalNote(id, text) {
    const ticket = tickets.find((item) => item.id === id);
    if (!ticket) throw new Error("Ticket not found");
    const note = {
      id: crypto.randomUUID(),
      author: CURRENT_AGENT,
      text,
      at: new Date().toISOString(),
    };
    ticket.notes.push(note);
    await delay(200);
    return note;
  },
  async getDashboardMetrics() {
    await delay();
    return {
      newTickets: tickets.filter((t) => t.status === "new").length,
      assignedToMe: tickets.filter((t) => t.assignedAgent === CURRENT_AGENT)
        .length,
      highPriority: tickets.filter((t) => t.priority.value === "high").length,
      critical: tickets.filter((t) => t.priority.value === "critical").length,
      escalated: tickets.filter((t) => t.status === "escalated").length,
      resolvedToday: 6,
      averageFirstResponse: "18 min",
      lowConfidence: tickets.filter((t) => t.requiresManualReview).length,
    };
  },
};
