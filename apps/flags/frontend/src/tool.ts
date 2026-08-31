import type { BadgeVariant } from "@platform/components/ui/badge";

export const TOOL_ID = "flags";
export const TITLE = "Feature Flags";
export const DESCRIPTION = "Create, roll out, and retire feature flags through a governed, audited path.";

export const STATE_VARIANTS: Record<string, BadgeVariant> = {
  draft: "secondary",
  active: "info",
  archived: "success",
};

export interface Flag {
  id: string;
  key: string;
  description: string;
  owner_team: string;
  state: string;
  staging_enabled: boolean;
  prod_enabled: boolean;
  prod_rollout_pct: number;
  created_at: string;
  updated_by: string | null;
  change_note: string | null;
}

export function asFlag(resource: Record<string, unknown>): Flag {
  return resource as unknown as Flag;
}
