import {
  createApiError,
  extractApiErrorCode,
  extractApiErrorMessage,
  normalizeApiError
} from "./errors";

describe("api error helpers", () => {
  it("extracts error message from backend payload", () => {
    expect(extractApiErrorMessage({ detail: "Request failed." })).toBe("Request failed.");
    expect(extractApiErrorMessage({ message: "Custom message." })).toBe("Custom message.");
    expect(extractApiErrorMessage({ detail: [{ msg: "Validation error." }] })).toBe(
      "Validation error."
    );
  });

  it("extracts error code from backend payload", () => {
    expect(extractApiErrorCode({ code: "E123" })).toBe("E123");
    expect(extractApiErrorCode({ error_code: "E999" })).toBe("E999");
    expect(extractApiErrorCode({})).toBeUndefined();
  });

  it("normalizes arbitrary thrown errors into ApiError", () => {
    const normalized = normalizeApiError(new Error("Network request failed."));
    expect(normalized.name).toBe("ApiError");
    expect(normalized.message).toBe("Network request failed.");
  });

  it("preserves ApiError objects when already normalized", () => {
    const apiError = createApiError({ message: "Already normalized.", status: 500 });
    const normalized = normalizeApiError(apiError);
    expect(normalized).toBe(apiError);
  });
});
