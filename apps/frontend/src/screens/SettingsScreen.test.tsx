import { act, fireEvent, render, waitFor } from "@testing-library/react-native";
import { Alert, AppState } from "react-native";
import { useIsFocused } from "@react-navigation/native";

import { getFitbitStatus, startFitbitOAuth, unlinkFitbit } from "../api/fitbit";
import SettingsScreen from "./SettingsScreen";

jest.mock("@react-navigation/native", () => ({
  ...jest.requireActual("@react-navigation/native"),
  useFocusEffect: jest.fn(),
  useIsFocused: jest.fn()
}));

jest.mock("../api/fitbit");

const mockedGetFitbitStatus = jest.mocked(getFitbitStatus);
const mockedStartFitbitOAuth = jest.mocked(startFitbitOAuth);
const mockedUnlinkFitbit = jest.mocked(unlinkFitbit);
const mockedUseIsFocused = jest.mocked(useIsFocused);

describe("SettingsScreen", () => {
  beforeEach(() => {
    jest.resetAllMocks();
    mockedUseIsFocused.mockReturnValue(true);
    mockedStartFitbitOAuth.mockResolvedValue();
    mockedUnlinkFitbit.mockResolvedValue({ success: true });
  });

  it("renders connect prompt when disconnected", async () => {
    mockedGetFitbitStatus.mockResolvedValue({
      connected: false
    });

    const { getByText } = render(<SettingsScreen />);

    await waitFor(() => {
      expect(getByText("Fitbit not connected")).toBeTruthy();
    });
    expect(getByText("Connect Fitbit")).toBeTruthy();
    expect(getByText("Disconnected")).toBeTruthy();
  });

  it("renders connected state when backend reports connected", async () => {
    mockedGetFitbitStatus.mockResolvedValue({
      connected: true,
      expiresAt: "2026-03-08T10:00:00Z",
      fitbitUserId: "fitbit-user-123",
      scopes: ["sleep", "heartrate"]
    });

    const { getByText } = render(<SettingsScreen />);

    await waitFor(() => {
      expect(getByText("Fitbit connected")).toBeTruthy();
    });
    expect(getByText("fitbit-user-123")).toBeTruthy();
    expect(getByText("Permissions")).toBeTruthy();
    expect(getByText("Sleep, Heart Rate")).toBeTruthy();
  });

  it("renders error state on API failure", async () => {
    mockedGetFitbitStatus.mockRejectedValue(new Error("Status request failed."));

    const { getByText } = render(<SettingsScreen />);

    await waitFor(() => {
      expect(getByText("Something went wrong")).toBeTruthy();
    });
    expect(getByText("Status request failed.")).toBeTruthy();
    expect(getByText("Try Again")).toBeTruthy();
  });

  it("calls OAuth start when connect is tapped", async () => {
    mockedGetFitbitStatus.mockResolvedValue({
      connected: false
    });

    const { getByText } = render(<SettingsScreen />);

    await waitFor(() => {
      expect(getByText("Connect Fitbit")).toBeTruthy();
    });

    fireEvent.press(getByText("Connect Fitbit"));

    await waitFor(() => {
      expect(mockedStartFitbitOAuth).toHaveBeenCalledTimes(1);
    });
  });

  it("calls unlink after disconnect is confirmed", async () => {
    mockedGetFitbitStatus
      .mockResolvedValueOnce({
        connected: true,
        fitbitUserId: "fitbit-user-321"
      })
      .mockResolvedValueOnce({
        connected: false
      });

    const { getByText } = render(<SettingsScreen />);

    await waitFor(() => {
      expect(getByText("Disconnect Fitbit")).toBeTruthy();
    });

    const alertSpy = jest.spyOn(Alert, "alert").mockImplementation(() => {});

    fireEvent.press(getByText("Disconnect Fitbit"));

    expect(alertSpy).toHaveBeenCalledWith(
      "Disconnect Fitbit?",
      "Disconnecting will stop new feature captures from Fitbit.",
      expect.any(Array)
    );

    const disconnectButtons = alertSpy.mock.calls[0]?.[2];
    const disconnectAction = Array.isArray(disconnectButtons)
      ? disconnectButtons.find((button) => button.text === "Disconnect")
      : null;

    act(() => {
      disconnectAction?.onPress?.();
    });

    await waitFor(() => {
      expect(mockedUnlinkFitbit).toHaveBeenCalledTimes(1);
    });

    alertSpy.mockRestore();
  });

  it("reloads status when app returns to active state", async () => {
    let appStateCallback: ((nextState: string) => void) | null = null;

    const addEventListenerSpy = jest
      .spyOn(AppState, "addEventListener")
      .mockImplementation((_eventType, callback) => {
        appStateCallback = callback as unknown as (nextState: string) => void;
        return { remove: jest.fn() } as { remove: () => void };
      });

    mockedGetFitbitStatus
      .mockResolvedValueOnce({ connected: false })
      .mockResolvedValueOnce({ connected: true, fitbitUserId: "fitbit-user-777" });

    const { getByText } = render(<SettingsScreen />);

    await waitFor(() => {
      expect(getByText("Fitbit not connected")).toBeTruthy();
    });

    act(() => {
      appStateCallback?.("background");
      appStateCallback?.("active");
    });

    await waitFor(() => {
      expect(mockedGetFitbitStatus).toHaveBeenCalledTimes(2);
    });

    addEventListenerSpy.mockRestore();
  });
});
