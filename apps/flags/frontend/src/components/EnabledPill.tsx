import { Badge } from "@platform/components/ui/badge";

export function EnabledPill({ enabled }: { enabled: boolean }) {
  return <Badge variant={enabled ? "success" : "secondary"}>{enabled ? "on" : "off"}</Badge>;
}
