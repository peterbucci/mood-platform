import { Linking } from "react-native";

type MockResponseOptions = {
  body?: unknown;
  status: number;
};

function createMockResponse({ body, status }: MockResponseOptions): Response {
  const rawBody =
    body === undefined ? "" : typeof body === "string" ? body : JSON.stringify(body);

  return {
    ok: status >= 200 && status < 300,
    status,
    text: jest.fn().mockResolvedValue(rawBody)
  } as unknown as Response;
}

describe("fitbit api module", () => {
  beforeEach(() => {
    jest.resetModules();
    process.env.EXPO_PUBLIC_API_BASE_URL = "http://api.example.test";
    global.fetch = jest.fn();
    jest.spyOn(Linking, "canOpenURL").mockResolvedValue(true);
    jest.spyOn(Linking, "openURL").mockResolvedValue();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("fetches Fitbit status from the expected endpoint", async () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { getFitbitStatus } = require("./fitbit");
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      createMockResponse({
        body: {
          connected: true,
          fitbitUserId: "fitbit-user-1",
          lastSyncAt: "2026-03-06T12:00:00Z",
          scopes: ["activity", "sleep"]
        },
        status: 200
      })
    );

    const status = await getFitbitStatus();

    expect(status.connected).toBe(true);
    expect(global.fetch).toHaveBeenCalledWith(
      "http://api.example.test/fitbit/oauth/status",
      expect.objectContaining({ method: "GET" })
    );
  });

  it("opens Fitbit OAuth start URL using configured base URL", async () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { startFitbitOAuth } = require("./fitbit");
    await startFitbitOAuth();

    expect(Linking.canOpenURL).toHaveBeenCalledWith("http://api.example.test/fitbit/oauth/start");
    expect(Linking.openURL).toHaveBeenCalledWith("http://api.example.test/fitbit/oauth/start");
  });

  it("calls unlink endpoint", async () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { unlinkFitbit } = require("./fitbit");
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      createMockResponse({ body: { success: true }, status: 200 })
    );

    const payload = await unlinkFitbit();

    expect(payload.success).toBe(true);
    expect(global.fetch).toHaveBeenCalledWith(
      "http://api.example.test/fitbit/oauth/unlink",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("fetches Fitbit integration settings from the expected endpoint", async () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { getFitbitSettings } = require("./fitbit");
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      createMockResponse({
        body: {
          clientId: "fitbit-client-id",
          clientSecretMasked: "********1234",
          redirectUri: "http://localhost:8000/fitbit/oauth/callback",
          scope: "activity sleep",
          subscriberId: "subscriber-1",
          webhookSecretMasked: "********9876",
          hasClientSecret: true,
          hasWebhookSecret: true
        },
        status: 200
      })
    );

    const settings = await getFitbitSettings();

    expect(settings.clientId).toBe("fitbit-client-id");
    expect(settings.clientSecretMasked).toBe("********1234");
    expect(global.fetch).toHaveBeenCalledWith(
      "http://api.example.test/settings/fitbit",
      expect.objectContaining({ method: "GET" })
    );
  });

  it("updates Fitbit integration settings using PUT /settings/fitbit", async () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { updateFitbitSettings } = require("./fitbit");
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      createMockResponse({
        body: {
          clientId: "fitbit-client-id",
          clientSecretMasked: "********1234",
          redirectUri: "http://localhost:8000/fitbit/oauth/callback",
          scope: "activity sleep",
          subscriberId: "subscriber-1",
          webhookSecretMasked: "********9876",
          hasClientSecret: true,
          hasWebhookSecret: true
        },
        status: 200
      })
    );

    const payload = await updateFitbitSettings({
      clientId: "fitbit-client-id",
      clientSecret: "new-secret",
      redirectUri: "http://localhost:8000/fitbit/oauth/callback",
      scope: "activity sleep",
      subscriberId: "subscriber-1",
      webhookSecret: "webhook-secret"
    });

    expect(payload.clientId).toBe("fitbit-client-id");
    expect(global.fetch).toHaveBeenCalledWith(
      "http://api.example.test/settings/fitbit",
      expect.objectContaining({
        body: JSON.stringify({
          clientId: "fitbit-client-id",
          clientSecret: "new-secret",
          redirectUri: "http://localhost:8000/fitbit/oauth/callback",
          scope: "activity sleep",
          subscriberId: "subscriber-1",
          webhookSecret: "webhook-secret"
        }),
        method: "PUT"
      })
    );
  });
});
