import type { FitbitConnectionStatus } from "../types/fitbit";

type FitbitConnectionTone = "success" | "neutral" | "warning";

type FitbitConnectionPresentation = {
  description: string;
  statusLabel: string;
  tone: FitbitConnectionTone;
  title: string;
};

const FRIENDLY_SCOPE_LABELS: Record<string, string> = {
  activity: "Activity",
  electrocardiogram: "ECG",
  heartrate: "Heart Rate",
  location: "Location",
  nutrition: "Nutrition",
  oxygensaturation: "Oxygen Saturation",
  profile: "Profile",
  respiratoryrate: "Respiratory Rate",
  settings: "Settings",
  sleep: "Sleep",
  social: "Social",
  temperature: "Temperature",
  weight: "Weight"
};

function parseTimestamp(value: string | null | undefined): number | null {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  return parsed.getTime();
}

function formatDuration(diffMs: number): string {
  const diffMinutes = Math.round(diffMs / 60000);
  if (diffMinutes < 60) {
    return `${Math.max(diffMinutes, 1)} min`;
  }

  const diffHours = Math.round(diffMs / 3600000);
  if (diffHours < 24) {
    return `${diffHours} hour${diffHours === 1 ? "" : "s"}`;
  }

  const diffDays = Math.round(diffMs / 86400000);
  return `${diffDays} day${diffDays === 1 ? "" : "s"}`;
}

export function formatFitbitTimestamp(
  value: string | null | undefined,
  nowMs: number = Date.now()
): string {
  const timestamp = parseTimestamp(value);
  if (timestamp === null) {
    return "N/A";
  }

  const parsed = new Date(timestamp);
  const now = new Date(nowMs);
  const isSameYear = parsed.getFullYear() === now.getFullYear();
  const formatOptions: Intl.DateTimeFormatOptions = {
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    month: "short"
  };

  if (!isSameYear) {
    formatOptions.year = "numeric";
  }

  return parsed.toLocaleString(undefined, formatOptions);
}

export function formatFitbitRelativeTime(
  value: string | null | undefined,
  nowMs: number = Date.now()
): string | null {
  const timestamp = parseTimestamp(value);
  if (timestamp === null) {
    return null;
  }

  const diffMs = nowMs - timestamp;
  if (diffMs < 45000) {
    return "Just now";
  }

  if (diffMs < 0) {
    return formatFitbitTimestamp(value, nowMs);
  }

  return `${formatDuration(diffMs)} ago`;
}

export function formatFitbitExpirationHint(
  value: string | null | undefined,
  nowMs: number = Date.now()
): string {
  const timestamp = parseTimestamp(value);
  if (timestamp === null) {
    return "Expiration unavailable";
  }

  const diffMs = timestamp - nowMs;
  if (diffMs <= 0) {
    return "Expired";
  }

  return `Expires in ${formatDuration(diffMs)}`;
}

export function formatFitbitPermission(scope: string): string {
  const normalizedKey = scope.toLowerCase().replace(/[\s._-]+/g, "");
  const friendlyLabel = FRIENDLY_SCOPE_LABELS[normalizedKey];
  if (friendlyLabel) {
    return friendlyLabel;
  }

  return scope
    .trim()
    .replace(/[\s._-]+/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

export function formatFitbitPermissionsPreview(scopes: string[], limit: number = 4): string {
  const labels = Array.from(new Set(scopes.map(formatFitbitPermission)));
  if (labels.length <= limit) {
    return labels.join(", ");
  }

  return `${labels.slice(0, limit).join(", ")} +${labels.length - limit} more`;
}

export function getFitbitConnectionPresentation(
  status: FitbitConnectionStatus,
  nowMs: number = Date.now()
): FitbitConnectionPresentation {
  if (!status.connected) {
    return {
      description:
        "Connect your Fitbit account to automatically capture activity, sleep, and recovery features.",
      statusLabel: "Disconnected",
      title: "Fitbit not connected",
      tone: "neutral"
    };
  }

  const expiresAt = parseTimestamp(status.expiresAt);
  if (expiresAt !== null && expiresAt <= nowMs) {
    return {
      description: "Your Fitbit connection has expired. Reconnect to keep capturing new Fitbit features.",
      statusLabel: "Expired",
      title: "Fitbit needs attention",
      tone: "warning"
    };
  }

  return {
    description: "Your Fitbit account is linked and ready to capture features.",
    statusLabel: "Connected",
    title: "Fitbit connected",
    tone: "success"
  };
}
