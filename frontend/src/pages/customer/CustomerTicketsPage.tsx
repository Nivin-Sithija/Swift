import { useEffect, useMemo, useState } from "react";
import { PageHeader } from "../../components/layout/Layouts";
import {
  EmptyState,
  ErrorState,
  LoadingSkeleton,
  Pagination,
  TicketCards,
  TicketFilters,
  TicketTable,
  TicketTableSkeleton,
} from "../../components/tickets/TicketComponents";
import { ticketService } from "../../services/serviceSelector";
import type { Ticket } from "../../types";
import { filterTickets } from "../../lib/utils";
import { EMPTY_FILTERS } from "../../lib/constants";
import { useLanguage } from "../../app/providers/LanguageProvider";
const PAGE_SIZE = 6;
export function CustomerTicketsPage() {
  const { tr } = useLanguage();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [filters, setFilters] = useState(EMPTY_FILTERS);
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
  useEffect(load, []);
  const filtered = useMemo(
    () => filterTickets(tickets, filters),
    [tickets, filters],
  );
  const shown = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  return (
    <>
      <PageHeader
        eyebrow={tr("Support history")}
        title={tr("My tickets")}
        description={tr("Track requests, status updates, and approved responses.")}
      />
      <div className="card list-card">
        <TicketFilters
          filters={filters}
          onChange={(p) => {
            setFilters((v) => ({ ...v, ...p }));
            setPage(1);
          }}
          onClear={() => setFilters(EMPTY_FILTERS)}
        />
        {loading ? (
          <><div className="desktop-only"><TicketTableSkeleton /></div><div className="mobile-list"><LoadingSkeleton /></div></>
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
            <div className="desktop-only">
              <TicketTable tickets={shown} />
            </div>
            <div className="mobile-list">
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
    </>
  );
}
