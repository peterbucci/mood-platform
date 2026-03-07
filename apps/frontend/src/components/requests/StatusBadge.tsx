import type { RequestStatus } from "../../types/requests";
import AppStatusBadge from "../ui/StatusBadge";

type StatusBadgeProps = {
  status: RequestStatus;
};

function getLabel(status: RequestStatus): string {
  if (status === "fulfilled") {
    return "Fulfilled";
  }
  if (status === "canceled") {
    return "Canceled";
  }
  return "Pending";
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  return <AppStatusBadge label={getLabel(status)} tone={status} />;
}
