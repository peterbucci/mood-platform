import { fireEvent, render, waitFor } from "@testing-library/react-native";

import MoodLabelEditor from "./MoodLabelEditor";

describe("MoodLabelEditor", () => {
  it("prefills editor fields when feature already has label", async () => {
    const onSaveLabel = jest.fn().mockResolvedValue(undefined);

    const { getByTestId, getByText } = render(
      <MoodLabelEditor
        initialLabel={{ category: "calm", emotion: "Relaxed" }}
        onSaveLabel={onSaveLabel}
      />
    );

    await waitFor(() => {
      expect(getByText("Update Mood Label")).toBeTruthy();
      expect(getByTestId("mood-category-option-calm")).toBeTruthy();
      expect(getByTestId("mood-emotion-option-relaxed")).toBeTruthy();
    });
  });

  it("shows empty form for unlabeled feature", async () => {
    const onSaveLabel = jest.fn().mockResolvedValue(undefined);

    const { getByText } = render(
      <MoodLabelEditor initialLabel={undefined} onSaveLabel={onSaveLabel} />
    );

    await waitFor(() => {
      expect(getByText("Add Mood Label")).toBeTruthy();
      expect(getByText("Select a category first.")).toBeTruthy();
    });
  });

  it("updates emotion options when category changes", async () => {
    const onSaveLabel = jest.fn().mockResolvedValue(undefined);

    const { getByTestId, queryByTestId } = render(
      <MoodLabelEditor initialLabel={undefined} onSaveLabel={onSaveLabel} />
    );

    fireEvent.press(getByTestId("mood-category-option-calm"));

    await waitFor(() => {
      expect(getByTestId("mood-emotion-option-peaceful")).toBeTruthy();
    });

    fireEvent.press(getByTestId("mood-category-option-stressed"));

    await waitFor(() => {
      expect(getByTestId("mood-emotion-option-anxious")).toBeTruthy();
      expect(queryByTestId("mood-emotion-option-peaceful")).toBeNull();
    });
  });

  it("saves a valid mood label", async () => {
    const onSaveLabel = jest.fn().mockResolvedValue(undefined);

    const { getByTestId } = render(
      <MoodLabelEditor initialLabel={undefined} onSaveLabel={onSaveLabel} />
    );

    fireEvent.press(getByTestId("mood-category-option-energized"));
    fireEvent.press(getByTestId("mood-save-button"));

    await waitFor(() => {
      expect(onSaveLabel).toHaveBeenCalledWith("energized", "Happy");
    });
  });

  it("prevents duplicate submissions while save is in flight", async () => {
    let resolveSave: (() => void) | null = null;
    const onSaveLabel = jest.fn().mockImplementation(
      () =>
        new Promise<void>((resolve) => {
          resolveSave = resolve;
        })
    );

    const { getByTestId } = render(
      <MoodLabelEditor initialLabel={undefined} onSaveLabel={onSaveLabel} />
    );

    fireEvent.press(getByTestId("mood-category-option-calm"));
    fireEvent.press(getByTestId("mood-save-button"));
    fireEvent.press(getByTestId("mood-save-button"));

    expect(onSaveLabel).toHaveBeenCalledTimes(1);

    resolveSave?.();

    await waitFor(() => {
      expect(onSaveLabel).toHaveBeenCalledTimes(1);
    });
  });

  it("shows user-friendly error when save fails", async () => {
    const onSaveLabel = jest.fn().mockRejectedValue(new Error("Save rejected by backend."));

    const { getByTestId, getByText } = render(
      <MoodLabelEditor initialLabel={undefined} onSaveLabel={onSaveLabel} />
    );

    fireEvent.press(getByTestId("mood-category-option-tired"));
    fireEvent.press(getByTestId("mood-save-button"));

    await waitFor(() => {
      expect(getByText("Save rejected by backend.")).toBeTruthy();
    });
  });
});
