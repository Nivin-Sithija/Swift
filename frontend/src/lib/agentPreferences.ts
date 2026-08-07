export type AgentPreferences = {
  defaultQueueView: "all" | "high" | "escalated";
  pageSize: "8" | "16" | "24";
  desktopNotifications: boolean;
  soundAlerts: boolean;
  compactQueue: boolean;
};

export const AGENT_PREFERENCES_KEY = "swift.agent.preferences";
export const DEFAULT_AGENT_PREFERENCES: AgentPreferences = {
  defaultQueueView: "all",
  pageSize: "8",
  desktopNotifications: true,
  soundAlerts: false,
  compactQueue: false,
};

export function loadAgentPreferences(): AgentPreferences {
  try {
    return {
      ...DEFAULT_AGENT_PREFERENCES,
      ...JSON.parse(localStorage.getItem(AGENT_PREFERENCES_KEY) ?? "{}"),
    };
  } catch {
    return DEFAULT_AGENT_PREFERENCES;
  }
}
