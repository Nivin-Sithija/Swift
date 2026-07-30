import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  CircleHelp,
  Clock3,
  Inbox,
  ShieldAlert,
  Siren,
  UserCheck,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "../../components/layout/Layouts";
import {
  ErrorState,
  LoadingSkeleton,
  TicketTable,
} from "../../components/tickets/TicketComponents";
import { mockTicketService } from "../../services/ticketService";
import type { DashboardMetrics, Ticket } from "../../types";
import { CURRENT_AGENT } from "../../lib/constants";
const chartData: Array<[string, number]> = [
  ["Card payments", 38],
  ["Transfers", 27],
  ["Cash withdrawal", 19],
  ["Account access", 13],
  ["Other", 8],
];
const greetingFor = (hour: number) =>
  hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
export function AgentDashboardPage() {
  const now = new Date();
  const today = new Intl.DateTimeFormat("en-LK", {
    weekday: "long",
    day: "numeric",
    month: "long",
  }).format(now);
  const greeting = greetingFor(now.getHours());
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [error, setError] = useState(false);
  const load = () => {
    setError(false);
    Promise.all([
      mockTicketService.getDashboardMetrics(),
      mockTicketService.getTickets(),
    ])
      .then(([m, t]) => {
        setMetrics(m);
        setTickets(t.slice(0, 6));
      })
      .catch((cause) => {
        console.error("[AgentDashboardPage/load]", cause);
        setError(true);
      });
  };
  useEffect(load, []);
  const cards = metrics
    ? ([
        ["New tickets", metrics.newTickets, Inbox, "primary"],
        ["Assigned to me", metrics.assignedToMe, UserCheck, "primary"],
        ["High priority", metrics.highPriority, AlertTriangle, "warning"],
        ["Critical", metrics.critical, ShieldAlert, "error"],
        ["Escalated", metrics.escalated, Siren, "warning"],
        ["Resolved today", metrics.resolvedToday, CheckCircle2, "success"],
        [
          "Avg. first response",
          metrics.averageFirstResponse,
          Clock3,
          "neutral",
        ],
        ["Low confidence", metrics.lowConfidence, CircleHelp, "neutral"],
      ] as const)
    : [];
  return (
    <>
      <PageHeader
        eyebrow={today}
        title={`${greeting}, ${CURRENT_AGENT.split(" ")[0]}`}
        description="Here is the state of your support operation right now."
        actions={
          <Link className="btn" to="/agent/tickets">
            Open queue <ArrowRight />
          </Link>
        }
      />
      {error ? (
        <ErrorState retry={load} />
      ) : !metrics ? (
        <LoadingSkeleton />
      ) : (
        <>
          <div className="metric-grid">
            {cards.map(([label, value, Icon, tone], i) => (
              <article
                className={`metric-card ${i === 3 ? "critical-metric" : ""}`}
                key={label}
              >
                <span className={`metric-icon tone-${tone}`}>
                  <Icon />
                </span>
                <div>
                  <span>{label}</span>
                  <strong>{value}</strong>
                  <small>
                    {i < 6 ? "Updated moments ago" : "Across open tickets"}
                  </small>
                </div>
              </article>
            ))}
          </div>
          <div className="chart-grid">
            <section className="card">
              <div className="card-heading">
                <div>
                  <span className="eyebrow">Distribution</span>
                  <h2>Tickets by category</h2>
                </div>
                <select aria-label="Chart period">
                  <option>Last 7 days</option>
                </select>
              </div>
              <div className="bar-chart">
                {chartData.map(([label, value]) => (
                  <div key={label}>
                    <span>{label}</span>
                    <div>
                      <i style={{ width: `${value * 2}%` }} />
                    </div>
                    <strong>{value}</strong>
                  </div>
                ))}
              </div>
            </section>
            <section className="card">
              <span className="eyebrow">Weekly volume</span>
              <h2>Ticket trend</h2>
              <div
                className="volume-chart"
                aria-label="Weekly ticket volume chart"
              >
                {[46, 62, 54, 78, 69, 88, 57].map((v, i) => (
                  <div key={i}>
                    <span style={{ height: `${v}%` }} />
                    <small>
                      {["Thu", "Fri", "Sat", "Sun", "Mon", "Tue", "Wed"][i]}
                    </small>
                  </div>
                ))}
              </div>
            </section>
            <section className="card language-panel">
              <span className="eyebrow">Language form</span>
              <h2>Multilingual mix</h2>
              {[
                ["English", "42%"],
                ["Sinhala", "18%"],
                ["Tamil", "14%"],
                ["Singlish", "12%"],
                ["Tanglish", "8%"],
                ["Mixed", "6%"],
              ].map(([x, v]) => (
                <div className="row spread" key={x}>
                  <span>{x}</span>
                  <strong>{v}</strong>
                </div>
              ))}
            </section>
          </div>
          <section className="card list-card">
            <div className="card-heading">
              <div>
                <span className="eyebrow">Needs attention</span>
                <h2>Recent ticket queue</h2>
              </div>
              <Link className="link-button" to="/agent/tickets">
                View full queue <ArrowRight />
              </Link>
            </div>
            <TicketTable tickets={tickets} agent />
          </section>
        </>
      )}
    </>
  );
}
