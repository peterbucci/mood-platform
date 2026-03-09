import { act, fireEvent, render, waitFor } from "@testing-library/react-native";
import { Alert, AppState } from "react-native";
import { useIsFocused } from "@react-navigation/native";

import {
  getFitbitSettings,
  getFitbitStatus,
  startFitbitOAuth,
  unlinkFitbit,
  updateFitbitSettings
} from "../api/fitbit";
import SettingsScreen from "./SettingsScreen";

jest.mock("@react-navigation/native", () => ({
  ...jest.requireActual("@react-navigation/native"),
  useFocusEffect: jest.fn(),
  useIsFocused: jest.fn()
}));

jest.mock("../api/fitbit");

const mockedGetFitbitStatus = jest.mocked(getFitbitStatus);
const mockedGetFitbitSettings = jest.mocked(getFitbitSettings);
const mockedStartFitbitOAuth = jest.mocked(startFitbitOAuth);
const mockedUnlinkFitbit = jest.mocked(unlinkFitbit);
const mockedUpdateFitbitSettings = jest.mocked(updateFitbitSettings);
const mockedUseIsFocused = jest.mocked(useIsFocused);

const DEFAULT_SETTINGS_PAYLOAD = {
  clientId: "fitbit-client-id",
  clientSecretMasked: "********1234",
  redirectUri: "http://localhost:8000/fitbit/oauth/callback",
  scope: "activity heartrate sleep",
  subscriberId: "subscriber-1",
  webhookSecretMasked: "********9876",
  hasClientSecret: true,
  hasWebhookSecret: true
};

describe("SettingsScreen", () => {
  beforeEach(() => {
    jest.resetAllMocks();
    mockedUseIsFocused.mockReturnValue(true);
    mockedGetFitbitSettings.mockResolvedValue(DEFAULT_SETTINGS_PAYLOAD);
    mockedStartFitbitOAuth.mockResolvedValue();
    mockedUnlinkFitbit.mockResolvedValue({ success: true });
    mockedUpdateFitbitSettings.mockResolvedValue(DEFAULT_SETTINGS_PAYLOAD);
  });

  it("renders connect prompt when disconnected", async () => {
    mockedGetFitbitStatus.mockResolvedValue({
      connected: false
    });

    const { getByDisplayValue, getByText } = render(<SettingsScreen />);

    await waitFor(() => {
      expect(getByText("Fitbit not connected")).toBeTruthy();
    });
    expect(getByText("Connect Fitbit")).toBeTruthy();
    expect(getByText("Disconnected")).toBeTruthy();
    expect(getByText("OAuth Configuration")).toBeTruthy();
    expect(getByDisplayValue("fitbit-client-id")).toBeTruthy();
    expect(getByDisplayValue("********1234")).toBeTruthy();
  });

  it("renders connected state when backend reports connected", async () => {
    mockedGetFitbitStatus.mockResolvedValue({
      connected: true,
      expiresAt: "2026-03-12T10:00:00Z",
      fitbitUserId: "fitbit-user-123",
      scopes: ["sleep", "heartrate"]
    });

    const { getByDisplayValue, getByText } = render(<SettingsScreen />);

    await waitFor(() => {
      expect(getByText("fitbit-user-123")).toBeTruthy();
    });
    expect(getByText("Fitbit connected")).toBeTruthy();
    expect(getByText("Permissions")).toBeTruthy();
    expect(getByText("Sleep, Heart Rate")).toBeTruthy();
    expect(getByDisplayValue("activity heartrate sleep")).toBeTruthy();
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

  it("saves Fitbit configuration changes and shows success feedback", async () => {
    mockedGetFitbitStatus.mockResolvedValue({ connected: false });
    mockedUpdateFitbitSettings.mockResolvedValue({
      ...DEFAULT_SETTINGS_PAYLOAD,
      clientId: "updated-client-id",
      redirectUri: "http://localhost:8000/fitbit/oauth/updated-callback",
      subscriberId: "subscriber-2"
    });

    const { getByDisplayValue, getByText } = render(<SettingsScreen />);

    await waitFor(() => {
      expect(getByText("Save Configuration")).toBeTruthy();
    });

    fireEvent.changeText(getByDisplayValue("fitbit-client-id"), "updated-client-id");
    fireEvent.changeText(
      getByDisplayValue("http://localhost:8000/fitbit/oauth/callback"),
      "http://localhost:8000/fitbit/oauth/updated-callback"
    );
    fireEvent.changeText(getByDisplayValue("subscriber-1"), "subscriber-2");

    fireEvent.press(getByText("Save Configuration"));

    await waitFor(() => {
      expect(mockedUpdateFitbitSettings).toHaveBeenCalledWith({
        clientId: "updated-client-id",
        redirectUri: "http://localhost:8000/fitbit/oauth/updated-callback",
        scope: "activity heartrate sleep",
        subscriberId: "subscriber-2",
        clientSecret: undefined,
        webhookSecret: undefined
      });
      expect(getByText("Configuration saved")).toBeTruthy();
      expect(getByText("Fitbit configuration saved.")).toBeTruthy();
    });
  });

  it("shows inline validation before saving incomplete Fitbit configuration", async () => {
    mockedGetFitbitStatus.mockResolvedValue({ connected: false });
    mockedGetFitbitSettings.mockResolvedValue({
      clientId: "",
      clientSecretMasked: null,
      redirectUri: "",
      scope: "activity heartrate sleep",
      subscriberId: "",
      webhookSecretMasked: null,
      hasClientSecret: false,
      hasWebhookSecret: false
    });

    const { getByText } = render(<SettingsScreen />);

    await waitFor(() => {
      expect(getByText("Save Configuration")).toBeTruthy();
    });

    fireEvent.press(getByText("Save Configuration"));

    await waitFor(() => {
      expect(getByText("Client ID is required.")).toBeTruthy();
      expect(getByText("Client Secret is required.")).toBeTruthy();
      expect(getByText("Redirect URI is required.")).toBeTruthy();
    });

    expect(mockedUpdateFitbitSettings).not.toHaveBeenCalled();
  });
});
