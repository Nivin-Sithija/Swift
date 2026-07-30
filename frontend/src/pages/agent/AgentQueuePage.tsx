import { AlertTriangle, CheckCircle2, UserRoundPlus } from "lucide-react";
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
} from "../../components/tickets/TicketComponents";
import { filterTickets, sortTickets, type TicketSort } from "../../lib/utils";
import { mockTicketService } from "../../services/ticketService";
import type { Ticket } from "../../types";
import { CURRENT_AGENT, EMPTY_FILTERS } from "../../lib/constants";
const PAGE_SIZE = 8;
export function AgentQueuePage({
  mode = "all",
}: {
  mode?: "all" | "high" | "escalated" | "resolved";
}) {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [selected, setSelected] = useState<string[]>([]);
  const [page, setPage] = useState(1);
  const [notice, setNotice] = useState("");
  const [sort, setSort] = useState<TicketSort>("priority");
  const load = () => {
    setLoading(true);
    setError(false);
    mockTicketService
      .getTickets()
      .then(setTickets)
      .catch((cause) => {
        console.error("[AgentQueuePage/load]", cause);
        setError(true);
      })
      .finally(() => setLoading(false));
  };
  useEffect(load, []);
  const scoped = useMemo(
    () =>
      tickets.filter((t) =>
        mode === "high"
          ? ["high", "critical"].includes(t.priority.value) ||
            t.category.value.includes("fraud")
          : mode === "escalated"
            ? t.status === "escalated"
            : mode === "resolved"
              ? ["resolved", "closed"].includes(t.status)
              : true,
      ),
    [tickets, mode],
  );
  const filtered = useMemo(
    () => sortTickets(filterTickets(scoped, filters), sort),
    [scoped, filters, sort],
  );
  const shown = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const title =
    mode === "high"
      ? "High-priority review"
      : mode === "escalated"
        ? "Escalated tickets"
        : mode === "resolved"
          ? "Resolved tickets"
          : "Ticket queue";
  return (
    <>
      <PageHeader
        eyebrow="Support operations"
        title={title}
        description={`${filtered.length} tickets · advisory predictions require agent judgement`}
        actions={
          <select
            aria-label="Sort tickets"
            value={sort}
            onChange={(e) => setSort(e.target.value as TicketSort)}
          >
            <option value="priority">Priority first</option>
            <option value="newest">Newest</option>
            <option value="confidence">Lowest confidence</option>
            <option value="waiting">Longest waiting</option>
          </select>
        }
      />
      {notice && (
        <div className="success-alert">
          <CheckCircle2 />
          {notice}
          <button onClick={() => setNotice("")}>Dismiss</button>
        </div>
      )}
      <div className="card list-card">
        <TicketFilters
          filters={filters}
          onChange={(p) => setFilters((v) => ({ ...v, ...p }))}
          onClear={() => setFilters(EMPTY_FILTERS)}
        />
        {selected.length > 0 && (
          <div className="bulk-bar">
            <strong>{selected.length} selected</strong>
            <button
              className="btn small"
              onClick={() =>
                setNotice(
                  `${selected.length} tickets assigned to ${CURRENT_AGENT}.`,
                )
              }
            >
              <UserRoundPlus />
              Assign to me
            </button>
            <button
              className="btn secondary small"
              onClick={() =>
                setNotice(
                  `${selected.length} tickets marked for escalation review.`,
                )
              }
            >
              <AlertTriangle />
              Escalate
            </button>
            <button className="link-button" onClick={() => setSelected([])}>
              Clear selection
            </button>
          </div>
        )}
        {loading ? (
          <LoadingSkeleton />
        ) : error ? (
          <ErrorState retry={load} />
        ) : shown.length === 0 ? (
          <EmptyState detail="No tickets match this queue and filter combination." />
        ) : (
          <>
            <div className="desktop-only">
              <TicketTable
                tickets={shown}
                agent
                selected={selected}
                onSelect={(id) =>
                  setSelected((v) =>
                    v.includes(id) ? v.filter((x) => x !== id) : [...v, id],
                  )
                }
              />
            </div>
            <div className="mobile-list">
              <TicketCards tickets={shown} agent />
            </div>
            <div className="table-footer">
              <span>
                Showing {shown.length} of {filtered.length} tickets
              </span>
              <Pagination
                page={page}
                pages={Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))}
                onChange={setPage}
              />
            </div>
          </>
        )}
      </div>
    </>
  );
}
