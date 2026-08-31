import { Badge, type BadgeVariant } from "./ui/badge";

export function StatusBadge({
  state,
  variants,
}: {
  state: string;
  variants: Record<string, BadgeVariant>;
}) {
  return (
    <Badge variant={variants[state] ?? "secondary"} className="capitalize">
      {state.replaceAll("_", " ")}
    </Badge>
  );
}
