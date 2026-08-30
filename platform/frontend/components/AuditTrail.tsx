import type { AuditRecord } from "../api/types";
import { Badge } from "./ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";

function outcomeVariant(outcome: string) {
  if (outcome === "success") return "success" as const;
  if (outcome === "permission_denied") return "destructive" as const;
  return "warning" as const;
}

export function AuditTrail({ records }: { records: AuditRecord[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Audit trail</CardTitle>
      </CardHeader>
      <CardContent>
        {records.length === 0 ? (
          <p className="text-sm text-muted-foreground">No activity yet.</p>
        ) : (
          <ol className="space-y-3">
            {records.map((r) => (
              <li key={r.id} className="flex flex-wrap items-center gap-2 border-b pb-3 text-sm last:border-0">
                <span className="text-muted-foreground">{new Date(r.ts).toLocaleString()}</span>
                <span className="font-medium">{r.actor_id}</span>
                <span className="text-muted-foreground">({r.actor_role})</span>
                <code className="rounded bg-muted px-1.5 py-0.5 text-xs">{r.action}</code>
                <Badge variant={outcomeVariant(r.outcome)}>{r.outcome.replaceAll("_", " ")}</Badge>
                {r.before_state && r.after_state && (
                  <span className="text-xs text-muted-foreground">
                    {r.before_state} → {r.after_state}
                  </span>
                )}
              </li>
            ))}
          </ol>
        )}
      </CardContent>
    </Card>
  );
}
