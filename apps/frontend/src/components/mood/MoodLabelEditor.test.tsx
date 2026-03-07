import { fireEvent, render, waitFor } from "@testing-library/react-native";

import MoodLabelEditor from "./MoodLabelEditor";

describe("MoodLabelEditor", () => {
  it("prefills the preview and selection when a label already exists", async () => {
    const onSaveLabel = jest.fn().mockResolvedValue(undefined);

    const { getAllByText, getByTestId, getByText } = render(
      <MoodLabelEditor
        initialLabel={{ category: "calm", emotion: "Relaxed" }}
        onSaveLabel={onSaveLabel}
      />
    );

    await waitFor(() => {
      expect(getByText("Mood Preview")).toBeTruthy();
      expect(getByText("Update Mood Label")).toBeTruthy();
      expect(getAllByText("Relaxed").length).toBeGreaterThan(0);
      expect(getByTestId("mood-category-option-calm")).toBeTruthy();
      expect(getByTestId("mood-emotion-option-relaxed")).toBeTruthy();
    });
  });

  it("shows an empty flow for an unlabeled feature", async () => {
    const onSaveLabel = jest.fn().mockResolvedValue(undefined);

    const { getByText } = render(
      <MoodLabelEditor initialLabel={undefined} onSaveLabel={onSaveLabel} />
    );

    await waitFor(() => {
      expect(getByText("Add Mood Label")).toBeTruthy();
      expect(getByText("Choose a category and emotion to preview the label before saving.")).toBeTruthy();
      expect(getByText("Choose a category to reveal matching emotions.")).toBeTruthy();
    });
  });

  it("updates emotion options and the live preview when category changes", async () => {
    const onSaveLabel = jest.fn().mockResolvedValue(undefined);

    const { getAllByText, getByTestId, getByText, queryByTestId } = render(
      <MoodLabelEditor initialLabel={undefined} onSaveLabel={onSaveLabel} />
    );

    fireEvent.press(getByTestId("mood-category-option-calm"));

    await waitFor(() => {
      expect(getByTestId("mood-emotion-option-peaceful")).toBeTruthy();
      expect(getByText("This is the label that will be saved to the snapshot.")).toBeTruthy();
    });

    fireEvent.press(getByTestId("mood-category-option-stressed"));
    fireEvent.press(getByTestId("mood-emotion-option-anxious"));

    await waitFor(() => {
      expect(getAllByText("Anxious").length).toBeGreaterThan(0);
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
    let resolveSave: ((value: void | PromiseLike<void>) => void) | undefined;
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

    expect(resolveSave).toBeDefined();
    resolveSave?.();

    await waitFor(() => {
      expect(onSaveLabel).toHaveBeenCalledTimes(1);
    });
  });

  it("shows a user-friendly error when save fails", async () => {
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
