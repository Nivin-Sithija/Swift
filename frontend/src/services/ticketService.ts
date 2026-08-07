import { mockTickets } from "../mocks/tickets";
import type {
  DashboardMetrics,
  AdminDashboardMetrics,
  AdminUserRecord, AdminQueue, AdminAudit, AdminSetting,
  InternalNote,
  Ticket,
  User,
  UserRole,
  TicketSubmission,
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
  register(input: { name: string; email: string; password: string; role: UserRole; preferredLanguage: "english" | "sinhala" | "tamil"; agentCode?: string }): Promise<User>;
  logout(): Promise<void>;
  createTicket?(submission: TicketSubmission): Promise<Ticket>;
  getTickets(): Promise<Ticket[]>;
  getTicket(id: string): Promise<Ticket>;
  getAdjacentTicketIds(id: string): Promise<AdjacentTickets>;
  updateTicket(id: string, patch: Partial<Ticket>): Promise<Ticket>;
  addInternalNote(id: string, text: string): Promise<InternalNote>;
  getDashboardMetrics(): Promise<DashboardMetrics>;
  getAdminDashboard(): Promise<AdminDashboardMetrics>;
  getAdminUsers(): Promise<AdminUserRecord[]>;
  updateAdminUser(id: string, patch: { role?: UserRole; is_active?: boolean }): Promise<AdminUserRecord>;
  getAdminQueues(): Promise<AdminQueue[]>;
  createAdminQueue(input: { name: string; description?: string }): Promise<AdminQueue>;
  updateAdminQueue(id: string, patch: { name?: string; description?: string; is_active?: boolean }): Promise<AdminQueue>;
  getAdminAudit(): Promise<AdminAudit[]>;
  getAdminSettings(): Promise<AdminSetting[]>;
  updateAdminSettings(values: Record<string,string>): Promise<AdminSetting[]>;
}

export const mockTicketService: TicketService = {
  async login(email, password, role) {
    await delay(500);
    if (email === "admin@swift.demo" && password === "password123")
      return { id: "admin-1", name: "Swift Admin", email, role: "administrator" };
    const expected =
      role === "agent" ? "agent@swift.demo" : "customer@swift.demo";
    if (email !== expected || password !== "password123")
      throw new Error("Invalid email or password");
    return role === "agent"
      ? { id: "agent-1", name: CURRENT_AGENT, email, role }
      : { id: "customer-1", name: "Maya Silva", email, role };
  },
  async register(input) {
    await delay(500);
    return { id: crypto.randomUUID(), name: input.name, email: input.email, role: input.role };
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
  async getAdminDashboard() {
    await delay();
    return {
      customers: 24, agents: 6, administrators: 2, activeSessions: 8,
      openTickets: tickets.filter((ticket) => !["resolved", "closed"].includes(ticket.status)).length,
      supportQueues: 3, auditEvents: 42,
      recentUsers: [
        { id: "customer-1", name: "Maya Silva", email: "customer@swift.demo", role: "customer" as const, isActive: true, createdAt: new Date().toISOString() },
        { id: "agent-1", name: CURRENT_AGENT, email: "agent@swift.demo", role: "agent" as const, isActive: true, createdAt: new Date().toISOString() },
      ],
    };
  },
  async getAdminUsers() { return (await this.getAdminDashboard()).recentUsers; },
  async updateAdminUser(id, patch) { const user=(await this.getAdminUsers()).find(x=>x.id===id)!; return {...user, role:patch.role??user.role, isActive:patch.is_active??user.isActive}; },
  async getAdminQueues() { return [{id:"general",name:"General Support",description:"Default queue",isActive:true,ticketCount:tickets.length}]; },
  async createAdminQueue(input) { return {id:crypto.randomUUID(),...input,isActive:true,ticketCount:0}; },
  async updateAdminQueue(id, patch) { return {id,name:patch.name??"Queue",description:patch.description,isActive:patch.is_active??true,ticketCount:0}; },
  async getAdminAudit() { return []; },
  async getAdminSettings() { return []; },
  async updateAdminSettings() { return []; },
};
