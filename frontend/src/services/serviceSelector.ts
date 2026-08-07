import { mockTicketService } from "./ticketService";
import { restTicketService } from "./restTicketService";
export const ticketService = import.meta.env.VITE_USE_MOCK_API === "false" ? restTicketService : mockTicketService;
