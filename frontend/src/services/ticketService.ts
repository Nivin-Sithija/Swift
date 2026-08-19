import type {
  AdminAudit, AdminDashboardMetrics, AdminQueue, AdminSetting, AdminUserRecord,
  DashboardMetrics, InternalNote, RagAssistanceResult, Ticket, TicketSubmission,
  User, UserRole,
} from "../types";

export interface AdjacentTickets {
  previous?: string;
  next?: string;
}

export interface TicketService {
  login(email: string, password: string, role: UserRole): Promise<User>;
  register(input: { name: string; email: string; password: string; role: UserRole; preferredLanguage: "english" | "sinhala" | "tamil"; agentCode?: string }): Promise<User>;
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
  updateAdminUser(id: string, patch: { role?: UserRole; is_active?: boolean }): Promise<AdminUserRecord>;
  getAdminQueues(): Promise<AdminQueue[]>;
  createAdminQueue(input: { name: string; description?: string }): Promise<AdminQueue>;
  updateAdminQueue(id: string, patch: { name?: string; description?: string; is_active?: boolean }): Promise<AdminQueue>;
  getAdminAudit(): Promise<AdminAudit[]>;
  getAdminSettings(): Promise<AdminSetting[]>;
  updateAdminSettings(values: Record<string, string>): Promise<AdminSetting[]>;
  getCustomerTicketAssistance(ticketId: string): Promise<RagAssistanceResult>;
}
