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

describe("features api module", () => {
  beforeEach(() => {
    jest.resetModules();
    process.env.EXPO_PUBLIC_API_BASE_URL = "http://api.example.test";
    global.fetch = jest.fn();
  });

  it("returns null when latest feature endpoint returns 404", async () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { getLatestFeature } = require("./features");
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      createMockResponse({ body: { detail: "No features found." }, status: 404 })
    );

    const latest = await getLatestFeature();
    expect(latest).toBeNull();
    expect(global.fetch).toHaveBeenCalledWith(
      "http://api.example.test/features/latest",
      expect.objectContaining({ method: "GET" })
    );
  });

  it("loads feature list and feature by id using expected paths", async () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { getFeatureById, getFeatures } = require("./features");
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce(
        createMockResponse({
          body: {
            items: [
              {
                createdAt: 1_772_800_000,
                data: { steps: 1000 },
                id: "f-1",
                source: "fitbit-pipeline",
                userId: "00000000-0000-0000-0000-000000000001"
              }
            ],
            limit: 20,
            offset: 0
          },
          status: 200
        })
      )
      .mockResolvedValueOnce(
        createMockResponse({
          body: {
            createdAt: 1_772_800_000,
            data: { steps: 1000 },
            id: "f-1",
            source: "fitbit-pipeline",
            userId: "00000000-0000-0000-0000-000000000001"
          },
          status: 200
        })
      );

    const list = await getFeatures();
    const byId = await getFeatureById("f-1");

    expect(list).toHaveLength(1);
    expect(byId.id).toBe("f-1");
    expect((global.fetch as jest.Mock).mock.calls[0][0]).toBe(
      "http://api.example.test/features?limit=20&offset=0"
    );
    expect((global.fetch as jest.Mock).mock.calls[1][0]).toBe(
      "http://api.example.test/features/f-1"
    );
  });

  it("deletes feature using DELETE /features/{id}", async () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { deleteFeature } = require("./features");
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      createMockResponse({ body: { id: "f-delete-1" }, status: 200 })
    );

    const response = await deleteFeature("f-delete-1");

    expect(response.id).toBe("f-delete-1");
    expect(global.fetch).toHaveBeenCalledWith(
      "http://api.example.test/features/f-delete-1",
      expect.objectContaining({ method: "DELETE" })
    );
  });
});
