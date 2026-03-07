export type ApiParseMode = "json" | "text" | "none";

export type ApiRequestOptions = Omit<RequestInit, "method" | "body"> & {
  allow404?: boolean;
  parseAs?: ApiParseMode;
};

export type ApiError = Error & {
  name: "ApiError";
  status?: number;
  code?: string;
  details?: unknown;
};
