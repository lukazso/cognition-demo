import type { ActionResponse, ApiError, ResourceDetail, ResourceList, Role, User } from "./types";

async function request<T>(path: string, role: Role, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-Mock-Role": role,
      ...init?.headers,
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    const error: ApiError = { status: response.status, detail: body.detail ?? response.statusText };
    throw error;
  }
  return response.json() as Promise<T>;
}

export function getMe(role: Role): Promise<User> {
  return request("/api/me", role);
}

export function listResources(toolId: string, role: Role): Promise<ResourceList> {
  return request(`/api/${toolId}/resources`, role);
}

export function getResource(toolId: string, resourceId: string, role: Role): Promise<ResourceDetail> {
  return request(`/api/${toolId}/resources/${resourceId}`, role);
}

/** Invoke a creating action: there is no resource yet, the server assigns the id. */
export function invokeCreateAction(
  toolId: string,
  actionName: string,
  role: Role,
  input: Record<string, unknown>,
): Promise<ActionResponse> {
  return request(`/api/${toolId}/resources/actions/${actionName}`, role, {
    method: "POST",
    body: JSON.stringify({ input, idempotency_key: crypto.randomUUID() }),
  });
}

export function invokeAction(
  toolId: string,
  resourceId: string,
  actionName: string,
  role: Role,
  input: Record<string, unknown>,
): Promise<ActionResponse> {
  return request(`/api/${toolId}/resources/${resourceId}/actions/${actionName}`, role, {
    method: "POST",
    body: JSON.stringify({ input, idempotency_key: crypto.randomUUID() }),
  });
}
