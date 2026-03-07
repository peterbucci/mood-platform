import { Linking } from "react-native";

import type { FitbitConnectionStatus, FitbitUnlinkResponse } from "../types/fitbit";
import { apiGet, apiPost, buildApiUrl } from "./client";
import { createApiError, normalizeApiError } from "./errors";

export async function getFitbitStatus(): Promise<FitbitConnectionStatus> {
  const payload = await apiGet<Partial<FitbitConnectionStatus>>("/fitbit/oauth/status");

  if (!payload || typeof payload.connected !== "boolean") {
    throw createApiError({ message: "Invalid Fitbit status payload." });
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
  try {
    const canOpen = await Linking.canOpenURL(oauthStartUrl);
    if (!canOpen) {
      throw createApiError({ message: "Unable to open Fitbit OAuth flow." });
    }
    await Linking.openURL(oauthStartUrl);
  } catch (error) {
    throw normalizeApiError(error, "Unable to start Fitbit OAuth.");
  }
}

export async function unlinkFitbit(): Promise<FitbitUnlinkResponse> {
  const payload = await apiPost<Partial<FitbitUnlinkResponse>>("/fitbit/oauth/unlink");
  if (!payload || typeof payload.success !== "boolean") {
    throw createApiError({ message: "Invalid Fitbit unlink response." });
  }
  return { success: payload.success };
}
