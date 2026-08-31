import type { BadgeVariant } from "./components/ui/badge";

/** Declarative description of a tool's UI. Apps provide one of these and the
 * platform's QueuePage / DetailPage render it — apps never build bespoke
 * tables, forms, or action plumbing. */
export interface ColumnDef {
  key: string;
  label: string;
}

export interface FieldDef {
  key: string;
  label: string;
}

export interface ActionField {
  key: string;
  label: string;
  kind: "text" | "textarea";
  required?: boolean;
  placeholder?: string;
}

export interface ActionDef {
  /** Short action name as used in the URL, e.g. "approve". */
  name: string;
  label: string;
  variant?: "default" | "destructive" | "outline" | "secondary";
  fields?: ActionField[];
}

export interface ToolFrontendConfig {
  toolId: string;
  title: string;
  description: string;
  resourceIdKey: string;
  columns: ColumnDef[];
  detailFields: FieldDef[];
  statusKey: string;
  statusVariants: Record<string, BadgeVariant>;
  actions: ActionDef[];
}
