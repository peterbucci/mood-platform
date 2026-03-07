const API_BASE_URL_ENV_KEY = "EXPO_PUBLIC_API_BASE_URL";

function validateBaseUrl(rawValue: string): string {
  const trimmed = rawValue.trim();
  if (!trimmed) {
    throw new Error(
      `${API_BASE_URL_ENV_KEY} is empty. Set it to your backend URL (example: http://192.168.1.10:8000).`
    );
  }

  let parsed: URL;
  try {
    parsed = new URL(trimmed);
  } catch {
    throw new Error(
      `${API_BASE_URL_ENV_KEY} must be a valid absolute URL (example: https://moodbackend.ngrok.app).`
    );
  }

  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error(`${API_BASE_URL_ENV_KEY} must use http or https.`);
  }

  return trimmed.replace(/\/+$/, "");
}

function resolveApiBaseUrl(): string {
  const rawValue = process.env[API_BASE_URL_ENV_KEY];
  if (!rawValue || !rawValue.trim()) {
    throw new Error(
      `Missing ${API_BASE_URL_ENV_KEY}. Add it to your frontend environment before starting Expo.`
    );
  }
  return validateBaseUrl(rawValue);
}

export const API_BASE_URL = resolveApiBaseUrl();
