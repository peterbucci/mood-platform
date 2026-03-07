export function shortenRequestId(requestId: string): string {
  if (requestId.length <= 18) {
    return requestId;
  }

  return `${requestId.slice(0, 4)}...${requestId.slice(-5)}`;
}

export function formatRequestSource(source: string): string {
  if (source === "fitbit-pipeline") {
    return "Fitbit";
  }

  return source
    .split(/[-_]+/)
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

export function formatRequestTimestamp(createdAt: number): string {
  const parsed = new Date(createdAt * 1000);
  if (Number.isNaN(parsed.getTime())) {
    return String(createdAt);
  }

  return parsed.toLocaleString(undefined, {
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    month: "short"
  });
}

export function formatRequestRelativeTime(createdAt: number, nowMs: number = Date.now()): string {
  const targetMs = createdAt * 1000;
  const diffMs = nowMs - targetMs;
  const minuteMs = 60 * 1000;
  const hourMs = 60 * minuteMs;
  const dayMs = 24 * hourMs;

  if (diffMs < minuteMs) {
    return "Just now";
  }

  if (diffMs < hourMs) {
    const minutes = Math.max(1, Math.floor(diffMs / minuteMs));
    return `${minutes}m ago`;
  }

  if (diffMs < dayMs) {
    const hours = Math.max(1, Math.floor(diffMs / hourMs));
    return `${hours}h ago`;
  }

  if (diffMs < dayMs * 7) {
    const days = Math.max(1, Math.floor(diffMs / dayMs));
    return `${days}d ago`;
  }

  return formatRequestTimestamp(createdAt);
}

export function isSameLocalDay(createdAt: number, nowMs: number = Date.now()): boolean {
  const createdAtDate = new Date(createdAt * 1000);
  const currentDate = new Date(nowMs);

  return (
    createdAtDate.getFullYear() === currentDate.getFullYear() &&
    createdAtDate.getMonth() === currentDate.getMonth() &&
    createdAtDate.getDate() === currentDate.getDate()
  );
}
