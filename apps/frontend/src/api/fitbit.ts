import { Linking } from "react-native";

import type { FitbitConnectionStatus, FitbitUnlinkResponse } from "../types/fitbit";

const DEFAULT_API_BASE_URL = "http://localhost:8000";

function getApiBaseUrl(): string {
  const configured = process.env.EXPO_PUBLIC_API_BASE_URL?.trim();
  if (configured) {
    return configured.replace(/\/+$/, "");
  }
  return DEFAULT_API_BASE_URL;
}

function buildApiUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${getApiBaseUrl()}${normalizedPath}`;
}

async function parseJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

export async function getFitbitStatus(): Promise<FitbitConnectionStatus> {
  const response = await fetch(buildApiUrl("/fitbit/oauth/status"), {
    headers: {
      Accept: "application/json"
    }
  });

  const payload = (await parseJson(response)) as Partial<FitbitConnectionStatus> | null;
  if (!response.ok) {
    const errorMessage =
      typeof payload?.message === "string" && payload.message.trim().length > 0
        ? payload.message
        : "Failed to fetch Fitbit status.";
    throw new Error(errorMessage);
  }

  if (!payload || typeof payload.connected !== "boolean") {
    throw new Error("Invalid Fitbit status payload.");
  }

  return {
    connected: payload.connected,
    expiresAt: payload.expiresAt ?? null,
    fitbitUserId: payload.fitbitUserId,
    scopes: Array.isArray(payload.scopes)
      ? payload.scopes.filter((scope): scope is string => typeof scope === "string")
      : undefined,
    lastSyncAt: payload.lastSyncAt ?? null,
    message: typeof payload.message === "string" ? payload.message : null
  };
}

export async function startFitbitOAuth(): Promise<void> {
  const oauthStartUrl = buildApiUrl("/fitbit/oauth/start");
  const canOpen = await Linking.canOpenURL(oauthStartUrl);
  if (!canOpen) {
    throw new Error("Unable to open Fitbit OAuth flow.");
  }
  await Linking.openURL(oauthStartUrl);
}

export async function unlinkFitbit(): Promise<FitbitUnlinkResponse> {
  const response = await fetch(buildApiUrl("/fitbit/oauth/unlink"), {
    headers: {
      Accept: "application/json"
    },
    method: "POST"
  });

  const payload = (await parseJson(response)) as Partial<FitbitUnlinkResponse> | null;
  if (!response.ok) {
    throw new Error("Failed to disconnect Fitbit.");
  }
  if (!payload || typeof payload.success !== "boolean") {
    throw new Error("Invalid Fitbit unlink response.");
  }
  return { success: payload.success };
}
