import AppCard from "../ui/AppCard";
import InfoText from "../ui/InfoText";

type ErrorStateProps = {
  message: string;
};

export default function ErrorState({ message }: ErrorStateProps) {
  return (
    <AppCard tone="danger">
      <InfoText tone="danger">Something went wrong</InfoText>
      <InfoText tone="danger">{message}</InfoText>
    </AppCard>
  );
}
