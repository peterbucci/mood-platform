describe("env configuration", () => {
  const originalApiBaseUrl = process.env.EXPO_PUBLIC_API_BASE_URL;

  beforeEach(() => {
    jest.resetModules();
  });

  afterEach(() => {
    if (originalApiBaseUrl) {
      process.env.EXPO_PUBLIC_API_BASE_URL = originalApiBaseUrl;
    } else {
      delete process.env.EXPO_PUBLIC_API_BASE_URL;
    }
  });

  it("loads and normalizes API base URL from env", () => {
    process.env.EXPO_PUBLIC_API_BASE_URL = "https://moodbackend.ngrok.app/";

    jest.isolateModules(() => {
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      const env = require("./env");
      expect(env.API_BASE_URL).toBe("https://moodbackend.ngrok.app");
    });
  });

  it("throws a clear error when API base URL is missing or empty", () => {
    process.env.EXPO_PUBLIC_API_BASE_URL = "   ";

    expect(() =>
      jest.isolateModules(() => {
        // eslint-disable-next-line @typescript-eslint/no-var-requires
        require("./env");
      })
    ).toThrow("Missing EXPO_PUBLIC_API_BASE_URL");
  });

  it("throws a clear error when API base URL is invalid", () => {
    process.env.EXPO_PUBLIC_API_BASE_URL = "not-a-valid-url";

    expect(() =>
      jest.isolateModules(() => {
        // eslint-disable-next-line @typescript-eslint/no-var-requires
        require("./env");
      })
    ).toThrow("EXPO_PUBLIC_API_BASE_URL must be a valid absolute URL");
  });
});
