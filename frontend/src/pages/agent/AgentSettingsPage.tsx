import { CheckCircle2, RotateCcw, Save } from "lucide-react";
import { useState } from "react";
import { PageHeader } from "../../components/layout/Layouts";
import {
  AGENT_PREFERENCES_KEY,
  DEFAULT_AGENT_PREFERENCES,
  loadAgentPreferences,
  type AgentPreferences,
} from "../../lib/agentPreferences";

export function AgentSettingsPage() {
  const [preferences, setPreferences] = useState(loadAgentPreferences);
  const [saved, setSaved] = useState(false);
  const update = <K extends keyof AgentPreferences>(key: K, value: AgentPreferences[K]) => {
    setPreferences((current) => ({ ...current, [key]: value }));
    setSaved(false);
  };
  const persist = () => {
    localStorage.setItem(AGENT_PREFERENCES_KEY, JSON.stringify(preferences));
    setSaved(true);
  };
  const reset = () => {
    setPreferences(DEFAULT_AGENT_PREFERENCES);
    localStorage.removeItem(AGENT_PREFERENCES_KEY);
    setSaved(true);
  };

  return (
    <>
      <PageHeader
        eyebrow="Personal workspace"
        title="Settings"
        description="Choose how your support queue behaves. These preferences apply only to this browser."
      />
      {saved && <div className="success-alert"><CheckCircle2 /> Preferences saved.</div>}
      <div className="chart-grid">
        <section className="card stack">
          <div><span className="eyebrow">Queue experience</span><h2>Ticket workspace</h2></div>
          <label>
            Default queue view
            <select value={preferences.defaultQueueView} onChange={(event) => update("defaultQueueView", event.target.value as AgentPreferences["defaultQueueView"])}>
              <option value="all">All tickets</option>
              <option value="high">High priority</option>
              <option value="escalated">Escalated</option>
            </select>
          </label>
          <label>
            Tickets per page
            <select value={preferences.pageSize} onChange={(event) => update("pageSize", event.target.value as AgentPreferences["pageSize"])}>
              <option value="8">8 tickets</option><option value="16">16 tickets</option><option value="24">24 tickets</option>
            </select>
          </label>
          <label className="row spread">
            <span><strong>Compact queue</strong><small>Reduce spacing to show more tickets.</small></span>
            <input type="checkbox" checked={preferences.compactQueue} onChange={(event) => update("compactQueue", event.target.checked)} />
          </label>
        </section>
        <section className="card stack">
          <div><span className="eyebrow">Attention controls</span><h2>Notifications</h2></div>
          <label className="row spread">
            <span><strong>Desktop notifications</strong><small>Alert me about newly assigned and escalated tickets.</small></span>
            <input type="checkbox" checked={preferences.desktopNotifications} onChange={(event) => update("desktopNotifications", event.target.checked)} />
          </label>
          <label className="row spread">
            <span><strong>Sound alerts</strong><small>Play a sound for critical tickets.</small></span>
            <input type="checkbox" checked={preferences.soundAlerts} onChange={(event) => update("soundAlerts", event.target.checked)} />
          </label>
          <p className="evidence-notice">Browser permission may still be required before desktop notifications can appear.</p>
        </section>
      </div>
      <div className="row end">
        <button className="btn ghost" onClick={reset}><RotateCcw /> Restore defaults</button>
        <button className="btn" onClick={persist}><Save /> Save preferences</button>
      </div>
    </>
  );
}
