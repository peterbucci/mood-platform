import type { ApiError } from "../types/api";

function asRecord(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function pickString(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : null;
}

export function extractApiErrorMessage(payload: unknown): string | null {
  const direct = pickString(payload);
  if (direct) {
    return direct;
  }

  const record = asRecord(payload);
  if (!record) {
    return null;
  }

  const fromTopLevel =
    pickString(record.message) ?? pickString(record.detail) ?? pickString(record.error);
  if (fromTopLevel) {
    return fromTopLevel;
  }

  const nestedDetail = asRecord(record.detail);
  if (nestedDetail) {
    return (
      pickString(nestedDetail.message) ??
      pickString(nestedDetail.detail) ??
      pickString(nestedDetail.error)
    );
  }

  if (Array.isArray(record.detail)) {
    const firstMessage = record.detail
      .map((item) => {
        const nested = asRecord(item);
        return nested ? pickString(nested.msg) ?? pickString(nested.message) : null;
      })
      .find((message): message is string => Boolean(message));

    if (firstMessage) {
      return firstMessage;
    }
  }

  return null;
}

export function extractApiErrorCode(payload: unknown): string | undefined {
  const record = asRecord(payload);
  if (!record) {
    return undefined;
  }

  return (
    pickString(record.code) ??
    pickString(record.errorCode) ??
    pickString(record.error_code) ??
    undefined
  );
}

export function createApiError({
  message,
  status,
  code,
  details
}: {
  message: string;
  status?: number;
  code?: string;
  details?: unknown;
}): ApiError {
  const error = new Error(message) as ApiError;
  error.name = "ApiError";
  error.status = status;
  error.code = code;
  error.details = details;
  return error;
}

export function isApiError(error: unknown): error is ApiError {
  return (
    error instanceof Error &&
    (error as ApiError).name === "ApiError" &&
    ("status" in error || "details" in error || "code" in error)
  );
}

export function normalizeApiError(
  error: unknown,
  fallbackMessage = "Request failed."
): ApiError {
  if (isApiError(error)) {
    return error;
  }

  if (error instanceof Error) {
    return createApiError({
      message: error.message || fallbackMessage,
      details: error
    });
  }

  return createApiError({
    message: fallbackMessage,
    details: error
  });
}
