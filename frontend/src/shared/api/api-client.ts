export type ApiErrorPayload = {
  error?: {
    code?: string;
    message?: string;
    details?: Record<string, unknown>;
  };
};

export type ApiRequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
};

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: Record<string, unknown>;

  constructor(params: {
    status: number;
    code: string;
    message: string;
    details?: Record<string, unknown>;
  }) {
    super(params.message);
    this.name = "ApiError";
    this.status = params.status;
    this.code = params.code;
    this.details = params.details ?? {};
  }
}

const API_BASE_URL = "/api/v1";

async function parseJsonResponse(response: Response): Promise<unknown> {
  if (response.status === 204) {
    return undefined;
  }

  const text = await response.text();

  if (!text) {
    return undefined;
  }

  return JSON.parse(text);
}

function buildApiError(response: Response, payload: unknown): ApiError {
  const errorPayload = payload as ApiErrorPayload;
  const error = errorPayload.error;

  return new ApiError({
    status: response.status,
    code: error?.code ?? "HTTP_ERROR",
    message: error?.message ?? "Ошибка запроса",
    details: error?.details
  });
}

export async function apiRequest<TResponse>(
  path: string,
  options: ApiRequestOptions = {}
): Promise<TResponse> {
  const headers = new Headers(options.headers);

  if (options.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    credentials: "include",
    body: options.body === undefined ? undefined : JSON.stringify(options.body)
  });

  const payload = await parseJsonResponse(response);

  if (!response.ok) {
    throw buildApiError(response, payload);
  }

  return payload as TResponse;
}
