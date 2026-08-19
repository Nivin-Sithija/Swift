import { mockTicketService } from "./ticketService";
import { restTicketService } from "./restTicketService";
import { isMockMode } from "../lib/config";

export const ticketService = isMockMode()
  ? mockTicketService
  : restTicketService;
