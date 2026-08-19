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
  humanize,
  LoadingSkeleton,
  TicketTable,
  TicketTableSkeleton,
} from "../../components/tickets/TicketComponents";
import { ticketService } from "../../services/serviceSelector";
import type { DashboardMetrics, Ticket } from "../../types";
import { useLanguage } from "../../app/providers/LanguageProvider";
import { useAuth } from "../../app/providers/AuthProvider";
import { loadAgentPreferences } from "../../lib/agentPreferences";
import { delay } from "../../lib/utils";
const DASHBOARD_LOADING_FLOOR_MS = 650;
const greetingFor = (hour: number) =>
  hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
export function AgentDashboardPage() {
  const { tr, language } = useLanguage();
  const { user } = useAuth();
  const now = new Date();
  const today = new Intl.DateTimeFormat(language === "si" ? "si-LK" : language === "ta" ? "ta-LK" : "en-LK", {
    weekday: "long",
    day: "numeric",
    month: "long",
  }).format(now);
  const greeting = tr(greetingFor(now.getHours()));
  const [preferences] = useState(loadAgentPreferences);
  const preferredQueuePath =
    preferences.defaultQueueView === "high"
      ? "/agent/high-priority"
      : preferences.defaultQueueView === "escalated"
        ? "/agent/escalated"
        : "/agent/tickets";
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [error, setError] = useState(false);
  const load = () => {
    setError(false);
    Promise.all([
      ticketService.getDashboardMetrics(),
      ticketService.getTickets(),
      delay(DASHBOARD_LOADING_FLOOR_MS),
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
        [tr("New tickets"), metrics.newTickets, Inbox, "primary"],
        [tr("Assigned to me"), metrics.assignedToMe, UserCheck, "primary"],
        [tr("High Priority"), metrics.highPriority, AlertTriangle, "warning"],
        [tr("Critical"), metrics.critical, ShieldAlert, "error"],
        [tr("Escalated"), metrics.escalated, Siren, "warning"],
        [tr("Resolved today"), metrics.resolvedToday, CheckCircle2, "success"],
        [
          "Avg. first response",
          metrics.averageFirstResponse,
          Clock3,
          "neutral",
        ],
        [tr("Low confidence"), metrics.lowConfidence, CircleHelp, "neutral"],
      ] as const)
    : [];
  const categoryMaximum = Math.max(
    1,
    ...(metrics?.categoryDistribution.map((item) => item.count) ?? []),
  );
  const volumeMaximum = Math.max(
    1,
    ...(metrics?.weeklyVolume.map((item) => item.count) ?? []),
  );
  const languageTotal =
    metrics?.languageDistribution.reduce((sum, item) => sum + item.count, 0) ?? 0;
  return (
    <>
      <PageHeader
        eyebrow={today}
        title={`${greeting}, ${user?.name.split(" ")[0] ?? "Agent"}`}
        description="Here is the state of your support operation right now."
        actions={
          <Link className="btn" to={preferredQueuePath}>
            {tr("Open queue")} <ArrowRight />
          </Link>
        }
      />
      {error ? (
        <ErrorState retry={load} />
      ) : !metrics ? (
        <div className="stack"><LoadingSkeleton /><section className="card list-card"><TicketTableSkeleton agent /></section></div>
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
                  <h2>{tr("Tickets by category")}</h2>
                </div>
                <select aria-label="Chart period">
                  <option>Last 7 days</option>
                </select>
              </div>
              <div className="bar-chart">
                {metrics.categoryDistribution.slice(0, 5).map((item) => (
                  <div key={item.label}>
                    <span>{humanize(item.label)}</span>
                    <div>
                      <i style={{ width: `${(item.count / categoryMaximum) * 100}%` }} />
                    </div>
                    <strong>{item.count}</strong>
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
                {metrics.weeklyVolume.map((item) => (
                  <div key={item.date}>
                    <span style={{ height: `${Math.max(4, (item.count / volumeMaximum) * 100)}%` }} title={`${item.count} tickets`} />
                    <small>
                      {new Intl.DateTimeFormat(language === "si" ? "si-LK" : language === "ta" ? "ta-LK" : "en-LK", { weekday: "short" }).format(new Date(`${item.date}T12:00:00`))}
                    </small>
                  </div>
                ))}
              </div>
            </section>
            <section className="card language-panel">
              <span className="eyebrow">Language form</span>
              <h2>{tr("Multilingual mix")}</h2>
              {metrics.languageDistribution.map((item) => (
                <div className="row spread" key={item.label}>
                  <span>{humanize(item.label)}</span>
                  <strong>{languageTotal ? Math.round((item.count / languageTotal) * 100) : 0}%</strong>
                </div>
              ))}
            </section>
          </div>
          <section className="card list-card">
            <div className="card-heading">
              <div>
                <span className="eyebrow">Needs attention</span>
                <h2>{tr("Recent ticket queue")}</h2>
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
