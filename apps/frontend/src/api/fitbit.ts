import { Linking } from "react-native";

import type {
  FitbitConnectionStatus,
  FitbitSettingsResponse,
  FitbitSettingsUpdatePayload,
  FitbitUnlinkResponse
} from "../types/fitbit";
import { apiGet, apiPost, apiPut, buildApiUrl } from "./client";
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

export async function getFitbitSettings(): Promise<FitbitSettingsResponse> {
  const payload = await apiGet<Partial<FitbitSettingsResponse>>("/settings/fitbit");
  if (
    !payload ||
    typeof payload.clientId !== "string" ||
    typeof payload.redirectUri !== "string" ||
    typeof payload.scope !== "string" ||
    typeof payload.subscriberId !== "string"
  ) {
    throw createApiError({ message: "Invalid Fitbit settings payload." });
  }

  return {
    clientId: payload.clientId,
    clientSecretMasked: payload.clientSecretMasked ?? null,
    redirectUri: payload.redirectUri,
    scope: payload.scope,
    subscriberId: payload.subscriberId,
    webhookSecretMasked: payload.webhookSecretMasked ?? null,
    hasClientSecret: Boolean(payload.hasClientSecret),
    hasWebhookSecret: Boolean(payload.hasWebhookSecret)
  };
}

export async function updateFitbitSettings(
  payload: FitbitSettingsUpdatePayload
): Promise<FitbitSettingsResponse> {
  const response = await apiPut<Partial<FitbitSettingsResponse>>("/settings/fitbit", payload);
  if (
    !response ||
    typeof response.clientId !== "string" ||
    typeof response.redirectUri !== "string" ||
    typeof response.scope !== "string" ||
    typeof response.subscriberId !== "string"
  ) {
    throw createApiError({ message: "Invalid Fitbit settings save response." });
  }

  return {
    clientId: response.clientId,
    clientSecretMasked: response.clientSecretMasked ?? null,
    redirectUri: response.redirectUri,
    scope: response.scope,
    subscriberId: response.subscriberId,
    webhookSecretMasked: response.webhookSecretMasked ?? null,
    hasClientSecret: Boolean(response.hasClientSecret),
    hasWebhookSecret: Boolean(response.hasWebhookSecret)
  };
}
