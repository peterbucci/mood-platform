import { API_BASE_URL } from "../config/env";
import type { ApiParseMode, ApiRequestOptions } from "../types/api";
import {
  createApiError,
  extractApiErrorCode,
  extractApiErrorMessage,
  normalizeApiError
} from "./errors";

function normalizePath(path: string): string {
  return path.startsWith("/") ? path : `/${path}`;
}

export function buildApiUrl(path: string): string {
  return `${API_BASE_URL}${normalizePath(path)}`;
}

function toRequestInitHeaders(
  inputHeaders: HeadersInit | undefined,
  includeJsonContentType: boolean
): Headers {
  const headers = new Headers(inputHeaders ?? {});
  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }
  if (includeJsonContentType && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  return headers;
}

async function parseResponseBody(response: Response, mode: ApiParseMode): Promise<unknown> {
  if (mode === "none") {
    return null;
  }

  const raw = await response.text();
  if (!raw.trim()) {
    return mode === "text" ? "" : null;
  }

  if (mode === "text") {
    return raw;
  }

  try {
    return JSON.parse(raw);
  } catch {
    if (response.ok) {
      throw createApiError({
        message: "Received malformed JSON response from API.",
        status: response.status,
        details: raw
      });
    }
    return raw;
  }
}

type InternalRequestOptions = ApiRequestOptions & {
  body?: unknown;
  method: "GET" | "POST" | "DELETE" | "PATCH" | "PUT";
  path: string;
};

async function apiRequest<T>({
  method,
  path,
  body,
  allow404 = false,
  parseAs = "json",
  ...requestInit
}: InternalRequestOptions): Promise<T | null> {
  let response: Response;
  try {
    response = await fetch(buildApiUrl(path), {
      ...requestInit,
      body: body === undefined ? undefined : JSON.stringify(body),
      headers: toRequestInitHeaders(requestInit.headers, body !== undefined),
      method
    });
  } catch (error) {
    throw normalizeApiError(error, "Network request failed.");
  }

  if (allow404 && response.status === 404) {
    return null;
  }

  const payload = await parseResponseBody(response, parseAs);
  if (!response.ok) {
    throw createApiError({
      message: extractApiErrorMessage(payload) ?? `Request failed with status ${response.status}.`,
      status: response.status,
      code: extractApiErrorCode(payload),
      details: payload
    });
  }

  return payload as T;
}

export async function apiGet<T>(
  path: string,
  options: Omit<ApiRequestOptions, "method"> & { allow404: true }
): Promise<T | null>;
export async function apiGet<T>(
  path: string,
  options?: Omit<ApiRequestOptions, "method">
): Promise<T>;
export async function apiGet<T>(
  path: string,
  options?: Omit<ApiRequestOptions, "method">
): Promise<T | null> {
  return apiRequest<T>({
    ...options,
    method: "GET",
    path
  });
}

export async function apiPost<T>(
  path: string,
  body?: unknown,
  options?: Omit<ApiRequestOptions, "method">
): Promise<T> {
  const response = await apiRequest<T>({
    ...options,
    body,
    method: "POST",
    path
  });

  return response as T;
}

export async function apiDelete<T>(
  path: string,
  options?: Omit<ApiRequestOptions, "method">
): Promise<T> {
  const response = await apiRequest<T>({
    ...options,
    method: "DELETE",
    path
  });

  return response as T;
}

export async function apiPatch<T>(
  path: string,
  body?: unknown,
  options?: Omit<ApiRequestOptions, "method">
): Promise<T> {
  const response = await apiRequest<T>({
    ...options,
    body,
    method: "PATCH",
    path
  });

  return response as T;
}

export async function apiPut<T>(
  path: string,
  body?: unknown,
  options?: Omit<ApiRequestOptions, "method">
): Promise<T> {
  const response = await apiRequest<T>({
    ...options,
    body,
    method: "PUT",
    path
  });

  return response as T;
}
