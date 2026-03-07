import { render } from "@testing-library/react-native";

import MoodLabelCard from "./MoodLabelCard";

describe("MoodLabelCard", () => {
  it("renders labeled mood category and emotion", () => {
    const { getByText } = render(
      <MoodLabelCard label={{ category: "energized", emotion: "Happy" }} />
    );

    expect(getByText("Mood")).toBeTruthy();
    expect(getByText("Energized")).toBeTruthy();
    expect(getByText("— Happy")).toBeTruthy();
  });

  it("renders unlabeled state when label is missing", () => {
    const { getByText } = render(<MoodLabelCard label={undefined} />);

    expect(getByText("Mood")).toBeTruthy();
    expect(getByText("Not labeled")).toBeTruthy();
  });

  it("renders unknown state for invalid category", () => {
    const { getByText } = render(<MoodLabelCard label={{ category: "wild", emotion: "Happy" }} />);

    expect(getByText("Mood")).toBeTruthy();
    expect(getByText("Unknown")).toBeTruthy();
  });

  it("renders unknown state for missing emotion", () => {
    const { getByText } = render(<MoodLabelCard label={{ category: "calm", emotion: null }} />);

    expect(getByText("Mood")).toBeTruthy();
    expect(getByText("Unknown")).toBeTruthy();
  });
});
