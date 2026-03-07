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

describe("requests api module", () => {
  beforeEach(() => {
    jest.resetModules();
    process.env.EXPO_PUBLIC_API_BASE_URL = "http://api.example.test";
    global.fetch = jest.fn();
  });

  it("creates feature request through POST /features/request", async () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { createFeatureRequest } = require("./requests");
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      createMockResponse({ body: { requestId: "r-1", status: "pending" }, status: 200 })
    );

    const response = await createFeatureRequest();

    expect(response).toEqual({ requestId: "r-1", status: "pending" });
    expect(global.fetch).toHaveBeenCalledWith(
      "http://api.example.test/features/request",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("loads requests and pending count from expected endpoints", async () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { getPendingRequestCount, getRequests } = require("./requests");
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce(
        createMockResponse({
          body: {
            items: [
              {
                createdAt: 1_772_800_000,
                featureId: null,
                id: "r-1",
                source: "fitbit-pipeline",
                status: "pending",
                userId: "00000000-0000-0000-0000-000000000001"
              }
            ],
            limit: 5,
            offset: 2
          },
          status: 200
        })
      )
      .mockResolvedValueOnce(createMockResponse({ body: { pendingCount: 3 }, status: 200 }));

    const requests = await getRequests(5, 2);
    const pendingCount = await getPendingRequestCount();

    expect(requests).toHaveLength(1);
    expect(pendingCount).toBe(3);
    expect((global.fetch as jest.Mock).mock.calls[0][0]).toBe(
      "http://api.example.test/requests?limit=5&offset=2"
    );
    expect((global.fetch as jest.Mock).mock.calls[1][0]).toBe(
      "http://api.example.test/requests/pending/count"
    );
  });

  it("cancels request using DELETE /requests/{id}", async () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { cancelRequest } = require("./requests");
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      createMockResponse({
        body: {
          createdAt: 1_772_800_000,
          featureId: null,
          id: "r-cancel",
          source: "fitbit-pipeline",
          status: "canceled",
          userId: "00000000-0000-0000-0000-000000000001"
        },
        status: 200
      })
    );

    const canceled = await cancelRequest("r-cancel");

    expect(canceled.status).toBe("canceled");
    expect(global.fetch).toHaveBeenCalledWith(
      "http://api.example.test/requests/r-cancel",
      expect.objectContaining({ method: "DELETE" })
    );
  });
});
