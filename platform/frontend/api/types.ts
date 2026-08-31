export type Role = "viewer" | "operator" | "supervisor";

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
}

export interface ResourceList {
  items: Record<string, unknown>[];
  total: number;
  available_create_actions: string[];
}

export interface AuditRecord {
  id: number;
  ts: string;
  actor_id: string;
  actor_role: string;
  action: string;
  resource_type: string;
  resource_id: string;
  outcome: string;
  error_kind: string | null;
  input_digest: string;
  before_state: string | null;
  after_state: string | null;
  detail: Record<string, unknown> | null;
}

export interface ResourceDetail {
  resource: Record<string, unknown>;
  available_actions: string[];
  audit: AuditRecord[];
}

export interface ActionResponse {
  resource: Record<string, unknown>;
  resource_id: string | null;
  new_state: string | null;
  replayed: boolean;
}

export interface ApiError {
  status: number;
  detail: { outcome: string; message: string } | string;
}

export function errorMessage(err: unknown): string {
  const e = err as ApiError;
  if (e && typeof e.detail === "object") return e.detail.message;
  if (e && typeof e.detail === "string") return e.detail;
  return "Request failed";
}
