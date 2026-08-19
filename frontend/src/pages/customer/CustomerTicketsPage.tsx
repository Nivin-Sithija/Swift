import { useEffect, useMemo, useState } from "react";
import { PageHeader } from "../../components/layout/Layouts";
import {
  EmptyState,
  ErrorState,
  LoadingSkeleton,
  Pagination,
  TicketCards,
  TicketTableSkeleton,
  humanize,
} from "../../components/tickets/TicketComponents";
import { ticketService } from "../../services/serviceSelector";
import type { Ticket } from "../../types";
import { TICKET_STATUSES } from "../../lib/constants";
import { useLanguage } from "../../app/providers/LanguageProvider";
const PAGE_SIZE = 6;
type TimeFilter = "all" | "7" | "30" | "90";
export function CustomerTicketGallery({
  refreshKey = 0,
}: {
  refreshKey?: number;
}) {
  const { tr } = useLanguage();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [status, setStatus] = useState("all");
  const [time, setTime] = useState<TimeFilter>("all");
  const [filterReferenceTime] = useState(() => Date.now());
  const [page, setPage] = useState(1);
  const load = () => {
    setLoading(true);
    setError(false);
    ticketService
      .getTickets()
      .then((data) => setTickets(data.slice(0, 10)))
      .catch((cause) => {
        console.error("[CustomerTicketsPage/load]", cause);
        setError(true);
      })
      .finally(() => setLoading(false));
  };
  useEffect(load, [refreshKey]);
  const filtered = useMemo(() => {
    const cutoff =
      time === "all" ? 0 : filterReferenceTime - Number(time) * 86_400_000;
    return tickets.filter(
      (ticket) =>
        (status === "all" || ticket.status === status) &&
        (!cutoff || new Date(ticket.createdAt).getTime() >= cutoff),
    );
  }, [tickets, status, time, filterReferenceTime]);
  const shown = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  return (
    <div className="card list-card customer-ticket-gallery">
      <div className="gallery-heading">
        <div>
          <span className="eyebrow">{tr("Support history")}</span>
          <h2>{tr("My tickets")}</h2>
        </div>
        <span className="ticket-count">{tickets.length}</span>
      </div>
      <div className="filters customer-gallery-filters">
        <select
          aria-label="Status filter"
          value={status}
          onChange={(event) => {
            setStatus(event.target.value);
            setPage(1);
          }}
        >
          <option value="all">{tr("All statuses")}</option>
          {TICKET_STATUSES.map((ticketStatus) => (
            <option key={ticketStatus} value={ticketStatus}>
              {tr(humanize(ticketStatus))}
            </option>
          ))}
        </select>
        <select
          aria-label="Time filter"
          value={time}
          onChange={(event) => {
            setTime(event.target.value as TimeFilter);
            setPage(1);
          }}
        >
          <option value="all">All time</option>
          <option value="7">Last 7 days</option>
          <option value="30">Last 30 days</option>
          <option value="90">Last 90 days</option>
        </select>
      </div>
      {loading ? (
        <>
          <div className="desktop-only">
            <TicketTableSkeleton />
          </div>
          <div className="mobile-list">
            <LoadingSkeleton />
          </div>
        </>
      ) : error ? (
        <ErrorState retry={load} />
      ) : shown.length === 0 ? (
        <EmptyState
          detail={
            tickets.length
              ? "No tickets match the selected filters."
              : "You have not submitted any tickets yet."
          }
        />
      ) : (
        <>
          <div className="ticket-gallery-list">
            <TicketCards tickets={shown} />
          </div>
          <Pagination
            page={page}
            pages={Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))}
            onChange={setPage}
          />
        </>
      )}
    </div>
  );
}

export function CustomerTicketsPage() {
  const { tr } = useLanguage();
  return (
    <>
      <PageHeader
        eyebrow={tr("Support history")}
        title={tr("My tickets")}
        description={tr(
          "Track requests, status updates, and approved responses.",
        )}
      />
      <CustomerTicketGallery />
    </>
  );
}
