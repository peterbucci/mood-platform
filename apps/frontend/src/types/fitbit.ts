export type FitbitConnectionStatus = {
  connected: boolean;
  expiresAt?: string | null;
  fitbitUserId?: string;
  scopes?: string[];
  lastSyncAt?: string | null;
  message?: string | null;
};

export type FitbitUnlinkResponse = {
  success: boolean;
};

export type FitbitSettingsResponse = {
  clientId: string;
  clientSecretMasked?: string | null;
  redirectUri: string;
  scope: string;
  subscriberId: string;
  webhookSecretMasked?: string | null;
  hasClientSecret?: boolean;
  hasWebhookSecret?: boolean;
};

export type FitbitSettingsUpdatePayload = {
  clientId: string;
  clientSecret?: string;
  redirectUri: string;
  scope?: string;
  subscriberId?: string;
  webhookSecret?: string;
};
