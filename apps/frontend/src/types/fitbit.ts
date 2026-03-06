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
