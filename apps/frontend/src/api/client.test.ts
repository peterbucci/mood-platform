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

describe("api client", () => {
  beforeEach(() => {
    jest.resetModules();
    process.env.EXPO_PUBLIC_API_BASE_URL = "http://api.example.test";
    global.fetch = jest.fn();
  });

  it("uses configured base URL for GET requests", () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      createMockResponse({ body: { ok: true }, status: 200 })
    );

    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { apiGet } = require("./client");
    return apiGet<{ ok: boolean }>("/health/live").then((payload: { ok: boolean }) => {
      expect(payload.ok).toBe(true);
      expect(global.fetch).toHaveBeenCalledWith(
        "http://api.example.test/health/live",
        expect.objectContaining({ method: "GET" })
      );
    });
  });

  it("sends JSON body and headers for POST requests", () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      createMockResponse({ body: { success: true }, status: 200 })
    );

    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { apiPost } = require("./client");
    return apiPost<{ success: boolean }>("/features/request", { source: "mobile-app" }).then(
      () => {
        const [, init] = (global.fetch as jest.Mock).mock.calls[0] as [string, RequestInit];
        const headers = init.headers as Headers;
        expect(init.method).toBe("POST");
        expect(init.body).toBe(JSON.stringify({ source: "mobile-app" }));
        expect(headers.get("Content-Type")).toBe("application/json");
      }
    );
  });

  it("normalizes non-2xx responses into ApiError", () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      createMockResponse({
        body: { code: "E_INTERNAL", detail: "Server error from backend." },
        status: 500
      })
    );

    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { apiGet } = require("./client");

    return expect(apiGet("/features/latest")).rejects.toMatchObject({
      code: "E_INTERNAL",
      message: "Server error from backend.",
      name: "ApiError",
      status: 500
    });
  });

  it("throws readable error when successful response is malformed JSON", () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      createMockResponse({ body: "not-json-response", status: 200 })
    );

    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { apiGet } = require("./client");
    return expect(apiGet("/requests")).rejects.toMatchObject({
      message: "Received malformed JSON response from API.",
      name: "ApiError"
    });
  });
});
