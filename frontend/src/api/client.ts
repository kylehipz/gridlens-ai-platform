export type ApiClientOptions = {
  baseUrl?: string;
  fetchImpl?: typeof fetch;
  getAccessToken?: () => string | null;
  getWorkspaceId?: () => string | null;
};

export type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
};

export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;
  readonly details?: unknown;

  constructor(message: string, status: number, code?: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export function createApiClient({
  baseUrl = "/api/v1",
  fetchImpl = fetch,
  getAccessToken = () => window.localStorage.getItem("gridlens.devAccessToken"),
  getWorkspaceId = () => window.localStorage.getItem("gridlens.devWorkspace")
}: ApiClientOptions = {}) {
  async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const headers = new Headers(options.headers);
    const token = getAccessToken();
    const workspaceId = getWorkspaceId();

    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    if (workspaceId) {
      headers.set("X-GridLens-Workspace", workspaceId);
    }
    if (options.body !== undefined && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }

    const response = await fetchImpl(`${baseUrl}${path}`, {
      ...options,
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body)
    });

    if (!response.ok) {
      throw await toApiError(response);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return (await response.json()) as T;
  }

  return {
    get: <T>(path: string, options?: RequestOptions) => request<T>(path, { ...options, method: "GET" }),
    post: <T>(path: string, body: unknown, options?: RequestOptions) =>
      request<T>(path, { ...options, method: "POST", body }),
    request
  };
}

async function toApiError(response: Response) {
  const fallback = response.statusText || "Request failed";
  const contentType = response.headers.get("Content-Type") ?? "";

  if (!contentType.includes("application/json")) {
    return new ApiError(fallback, response.status);
  }

  const payload = (await response.json().catch(() => null)) as
    | { message?: string; detail?: string; code?: string; details?: unknown }
    | null;

  return new ApiError(
    payload?.message ?? payload?.detail ?? fallback,
    response.status,
    payload?.code,
    payload?.details
  );
}

export const apiClient = createApiClient();
