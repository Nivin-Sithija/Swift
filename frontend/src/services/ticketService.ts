import { mockTickets } from "../mocks/tickets";
import type {
  DashboardMetrics,
  AdminDashboardMetrics,
  AdminUserRecord,
  AdminQueue,
  AdminAudit,
  AdminSetting,
  InternalNote,
  RagAssistanceResult,
  Ticket,
  User,
  UserRole,
  TicketSubmission,
} from "../types";
import { delay } from "../lib/utils";
import { CURRENT_AGENT } from "../lib/constants";

const tickets = structuredClone(mockTickets);
const MOCK_ACCOUNTS_KEY = "swift-mock-accounts";
export const MOCK_AGENT_REGISTRATION_CODE = "SWIFT-AGENT-2026";

type MockAccount = User & { password: string };

const readMockAccounts = (): MockAccount[] => {
  try {
    return JSON.parse(localStorage.getItem(MOCK_ACCOUNTS_KEY) || "[]") as MockAccount[];
  } catch {
    return [];
  }
};

const writeMockAccounts = (accounts: MockAccount[]) =>
  localStorage.setItem(MOCK_ACCOUNTS_KEY, JSON.stringify(accounts));

/** Neighbouring ticket ids in queue order, for the detail page's prev/next control. */
export interface AdjacentTickets {
  previous?: string;
  next?: string;
}

export interface TicketService {
  login(email: string, password: string, role: UserRole): Promise<User>;
  register(input: {
    name: string;
    email: string;
    password: string;
    role: UserRole;
    preferredLanguage: "english" | "sinhala" | "tamil";
    agentCode?: string;
  }): Promise<User>;
  logout(): Promise<void>;
  restoreSession(user: User): Promise<User>;
  createTicket?(submission: TicketSubmission): Promise<Ticket>;
  getTickets(): Promise<Ticket[]>;
  getTicket(id: string): Promise<Ticket>;
  getAdjacentTicketIds(id: string): Promise<AdjacentTickets>;
  updateTicket(id: string, patch: Partial<Ticket>): Promise<Ticket>;
  addInternalNote(id: string, text: string): Promise<InternalNote>;
  getDashboardMetrics(): Promise<DashboardMetrics>;
  getAdminDashboard(): Promise<AdminDashboardMetrics>;
  getAdminUsers(): Promise<AdminUserRecord[]>;
  updateAdminUser(
    id: string,
    patch: { role?: UserRole; is_active?: boolean },
  ): Promise<AdminUserRecord>;
  getAdminQueues(): Promise<AdminQueue[]>;
  createAdminQueue(input: {
    name: string;
    description?: string;
  }): Promise<AdminQueue>;
  updateAdminQueue(
    id: string,
    patch: { name?: string; description?: string; is_active?: boolean },
  ): Promise<AdminQueue>;
  getAdminAudit(): Promise<AdminAudit[]>;
  getAdminSettings(): Promise<AdminSetting[]>;
  updateAdminSettings(values: Record<string, string>): Promise<AdminSetting[]>;
  generateRagDraft(
    ticket: Ticket,
    institution: string,
  ): Promise<RagAssistanceResult>;
}

export const mockTicketService: TicketService = {
  async login(email, password, role) {
    await delay(500);
    const normalizedEmail = email.trim().toLowerCase();
    if (email === "admin@swift.demo" && password === "password123")
      return {
        id: "admin-1",
        name: "Swift Admin",
        email,
        role: "administrator",
      };
    const registered = readMockAccounts().find(
      (account) => account.email.toLowerCase() === normalizedEmail,
    );
    if (registered) {
      if (registered.password !== password || registered.role !== role)
        throw new Error("Invalid email or password");
      const { password: _password, ...user } = registered;
      return user;
    }
    const expected =
      role === "agent" ? "agent@swift.demo" : "customer@swift.demo";
    if (normalizedEmail !== expected || password !== "password123")
      throw new Error("Invalid email or password");
    return role === "agent"
      ? { id: "agent-1", name: CURRENT_AGENT, email, role }
      : { id: "customer-1", name: "Maya Silva", email, role };
  },
  async register(input) {
    await delay(500);
    const email = input.email.trim().toLowerCase();
    const accounts = readMockAccounts();
    const reservedEmails = ["admin@swift.demo", "agent@swift.demo", "customer@swift.demo"];
    if (reservedEmails.includes(email) || accounts.some((account) => account.email === email))
      throw new Error("An account with this email already exists");
    if (input.role === "agent" && input.agentCode !== MOCK_AGENT_REGISTRATION_CODE)
      throw new Error("Invalid support-agent registration code");
    const account: MockAccount = {
      id: crypto.randomUUID(),
      name: input.name,
      email,
      role: input.role,
      password: input.password,
    };
    writeMockAccounts([...accounts, account]);
    const { password: _password, ...user } = account;
    return user;
  },
  async logout() {
    await delay(100);
  },
  async restoreSession(user) {
    return user;
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
    const categoryCounts = new Map<string, number>();
    const languageCounts = new Map<string, number>();
    tickets.forEach((ticket) => {
      categoryCounts.set(
        ticket.category.value,
        (categoryCounts.get(ticket.category.value) ?? 0) + 1,
      );
      languageCounts.set(
        ticket.language,
        (languageCounts.get(ticket.language) ?? 0) + 1,
      );
    });
    const today = new Date();
    return {
      newTickets: tickets.filter((t) => t.status === "new").length,
      assignedToMe: tickets.filter((t) => t.assignedAgent === CURRENT_AGENT)
        .length,
      highPriority: tickets.filter((t) => t.priority.value === "high").length,
      critical: tickets.filter((t) => t.priority.value === "critical").length,
      escalated: tickets.filter((t) => t.status === "escalated").length,
      resolvedToday: tickets.filter(
        (ticket) =>
          ticket.status === "resolved" &&
          new Date(ticket.updatedAt).toDateString() === today.toDateString(),
      ).length,
      averageFirstResponse: (() => {
        const responseMinutes = tickets
          .filter((ticket) => ticket.approvedResponse)
          .map(
            (ticket) =>
              (new Date(ticket.approvedResponse!.approvedAt).getTime() -
                new Date(ticket.createdAt).getTime()) /
              60_000,
          )
          .filter((minutes) => minutes >= 0);
        return responseMinutes.length
          ? `${Math.round(responseMinutes.reduce((sum, value) => sum + value, 0) / responseMinutes.length)} min`
          : "Not available";
      })(),
      lowConfidence: tickets.filter((t) => t.requiresManualReview).length,
      categoryDistribution: [...categoryCounts]
        .map(([label, count]) => ({ label, count }))
        .sort((a, b) => b.count - a.count),
      languageDistribution: [...languageCounts]
        .map(([label, count]) => ({ label, count }))
        .sort((a, b) => b.count - a.count),
      weeklyVolume: Array.from({ length: 7 }, (_, index) => {
        const date = new Date(today);
        date.setDate(today.getDate() - (6 - index));
        return {
          date: date.toISOString().slice(0, 10),
          count: tickets.filter(
            (ticket) =>
              new Date(ticket.createdAt).toDateString() === date.toDateString(),
          ).length,
        };
      }),
    };
  },
  async getAdminDashboard() {
    await delay();
    return {
      customers: 24,
      agents: 6,
      administrators: 2,
      activeSessions: 8,
      openTickets: tickets.filter(
        (ticket) => !["resolved", "closed"].includes(ticket.status),
      ).length,
      supportQueues: 3,
      auditEvents: 42,
      recentUsers: [
        {
          id: "customer-1",
          name: "Maya Silva",
          email: "customer@swift.demo",
          role: "customer" as const,
          isActive: true,
          createdAt: new Date().toISOString(),
        },
        {
          id: "agent-1",
          name: CURRENT_AGENT,
          email: "agent@swift.demo",
          role: "agent" as const,
          isActive: true,
          createdAt: new Date().toISOString(),
        },
      ],
    };
  },
  async getAdminUsers() {
    return (await this.getAdminDashboard()).recentUsers;
  },
  async updateAdminUser(id, patch) {
    const user = (await this.getAdminUsers()).find((x) => x.id === id)!;
    return {
      ...user,
      role: patch.role ?? user.role,
      isActive: patch.is_active ?? user.isActive,
    };
  },
  async getAdminQueues() {
    return [
      {
        id: "general",
        name: "General Support",
        description: "Default queue",
        isActive: true,
        ticketCount: tickets.length,
      },
    ];
  },
  async createAdminQueue(input) {
    return {
      id: crypto.randomUUID(),
      ...input,
      isActive: true,
      ticketCount: 0,
    };
  },
  async updateAdminQueue(id, patch) {
    return {
      id,
      name: patch.name ?? "Queue",
      description: patch.description,
      isActive: patch.is_active ?? true,
      ticketCount: 0,
    };
  },
  async getAdminAudit() {
    return [];
  },
  async getAdminSettings() {
    return [];
  },
  async updateAdminSettings() {
    return [];
  },
  async generateRagDraft(ticket, institution) {
    await delay(600);
    if (["high", "critical"].includes(ticket.priority.value)) {
      return {
        route: "human_escalation",
        originalQuery: ticket.message,
        normalizedQuery: ticket.message.trim(),
        language: ticket.language,
        draft: null,
        citations: [],
        confidence: 0,
        escalationReason: "high_priority",
        approvalRequired: true,
        provider: null,
      };
    }
    return {
      route: "rag_draft",
      originalQuery: ticket.message,
      normalizedQuery: ticket.message.trim(),
      language: ticket.language,
      draft: `This mock RAG draft is scoped to ${institution}. [E1]`,
      citations: [
        {
          marker: "E1",
          sourceId: "MOCK-SRC-1",
          title: "Official product information",
          institution,
          url: "https://example.com",
          version: "1.0",
          reviewDate: "2026-07-29",
          chunkIds: ["mock-chunk-1"],
        },
      ],
      confidence: 0.82,
      escalationReason: null,
      approvalRequired: true,
      provider: "mock",
    };
  },

};
