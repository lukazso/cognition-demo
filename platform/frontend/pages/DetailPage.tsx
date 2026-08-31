import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getResource, invokeAction } from "../api/client";
import { errorMessage, type ResourceDetail } from "../api/types";
import { useRole } from "../auth/RoleContext";
import { ActionBar } from "../components/ActionBar";
import { AuditTrail } from "../components/AuditTrail";
import { StatusBadge } from "../components/StatusBadge";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import type { ToolFrontendConfig } from "../tool";

export function DetailPage({ config }: { config: ToolFrontendConfig }) {
  const { resourceId = "" } = useParams();
  const { role } = useRole();
  const [detail, setDetail] = useState<ResourceDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    getResource(config.toolId, resourceId, role)
      .then((d) => {
        setDetail(d);
        setError(null);
      })
      .catch((err) => setError(errorMessage(err)));
  }, [config.toolId, resourceId, role]);

  useEffect(load, [load]);

  if (error) return <p className="text-sm text-destructive">{error}</p>;
  if (!detail) return <p className="text-sm text-muted-foreground">Loading…</p>;

  const state = String(detail.resource[config.statusKey] ?? "");

  return (
    <div className="space-y-4">
      <Link to={`/${config.toolId}`} className="text-sm text-primary hover:underline">
        ← Back to queue
      </Link>
      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle>{resourceId}</CardTitle>
          <StatusBadge state={state} variants={config.statusVariants} />
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-3 md:grid-cols-3">
            {config.detailFields.map((f) => (
              <div key={f.key}>
                <dt className="text-xs font-medium uppercase text-muted-foreground">{f.label}</dt>
                <dd className="text-sm">{String(detail.resource[f.key] ?? "—")}</dd>
              </div>
            ))}
          </dl>
        </CardContent>
      </Card>
      <ActionBar
        actions={config.actions}
        availableActions={detail.available_actions}
        onInvoke={async (name, input) => {
          await invokeAction(config.toolId, resourceId, name, role, input);
          load();
        }}
      />
      <AuditTrail records={detail.audit} />
    </div>
  );
}
