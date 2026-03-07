import type { RequestStatus } from "../../types/requests";
import AppStatusBadge from "../ui/StatusBadge";

type StatusBadgeProps = {
  status: RequestStatus;
};

function getLabel(status: RequestStatus): string {
  if (status === "fulfilled") {
    return "Ready";
  }
  if (status === "canceled") {
    return "Canceled";
  }
  return "In progress";
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  return <AppStatusBadge label={getLabel(status)} tone={status} />;
}
