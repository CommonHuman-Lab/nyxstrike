let token: string | null = sessionStorage.getItem('nyxstrike_token');

function withAuthHeaders(headers: HeadersInit = {}): Headers {
  const merged = new Headers(headers);
  if (!merged.has('Content-Type')) {
    merged.set('Content-Type', 'application/json');
  }
  if (token) {
    merged.set('Authorization', `Bearer ${token}`);
  }
  return merged;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const timeoutMs = (() => {
    const headerTimeout = withAuthHeaders(init.headers).get('X-Request-Timeout-Seconds');
    const parsed = headerTimeout ? Number(headerTimeout) : NaN;
    if (Number.isFinite(parsed) && parsed > 0) return parsed * 1000;
    return 3_600_000;
  })();

  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);

  let res: Response;
  try {
    res = await fetch(path, {
      ...init,
      headers: withAuthHeaders(init.headers),
      signal: controller.signal,
    });
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error(`HTTP request timed out after ${Math.round(timeoutMs / 1000)}s`);
    }
    throw error;
  } finally {
    window.clearTimeout(timer);
  }

  if (res.status === 401) {
    clearToken();
    throw new Error('UNAUTHORIZED');
  }

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`HTTP ${res.status}: ${body}`);
  }

  return res.json() as Promise<T>;
}

export function setToken(value: string) {
  token = value;
  sessionStorage.setItem('nyxstrike_token', value);
}

export function clearToken() {
  token = null;
  sessionStorage.removeItem('nyxstrike_token');
}

export function hasToken(): boolean {
  return Boolean(token);
}

export function get<T>(path: string): Promise<T> {
  return request<T>(path);
}

export function post<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    body: body ? JSON.stringify(body) : undefined,
  });
}

export function postWithTimeout<T>(path: string, body: unknown, timeoutSeconds: number): Promise<T> {
  const headers = new Headers();
  headers.set('X-Request-Timeout-Seconds', String(timeoutSeconds));
  return request<T>(path, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });
}

export function patch<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
}

export function del<T>(path: string): Promise<T> {
  return request<T>(path, { method: 'DELETE' });
}

export function put<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: 'PUT',
    body: JSON.stringify(body),
  });
}

export function postFormData<T>(path: string, body: FormData): Promise<T> {
  // Do NOT set Content-Type — browser sets multipart/form-data + boundary automatically
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), 3_600_000);
  const headers = new Headers();
  if (token) headers.set('Authorization', `Bearer ${token}`);

  return fetch(path, { method: 'POST', headers, body, signal: controller.signal })
    .then(res => {
      window.clearTimeout(timer);
      if (res.status === 401) { clearToken(); throw new Error('UNAUTHORIZED'); }
      // Treat 409 conflict as a resolved value so callers can inspect { conflict: true }
      if (res.status === 409) return res.json() as Promise<T>;
      if (!res.ok) return res.text().then(t => { throw new Error(`HTTP ${res.status}: ${t}`); });
      return res.json() as Promise<T>;
    })
    .catch(err => { window.clearTimeout(timer); throw err; });
}

export function stream(path: string, query?: Record<string, string | number | boolean>): EventSource {
  if (!query || Object.keys(query).length === 0) {
    return new EventSource(path);
  }

  const params = new URLSearchParams();
  Object.entries(query).forEach(([key, value]) => params.set(key, String(value)));
  return new EventSource(`${path}?${params.toString()}`);
}
