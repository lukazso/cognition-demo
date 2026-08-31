import { useCallback, useEffect, useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";

import { getResource, invokeAction } from "@platform/api/client";
import { errorMessage, type ResourceDetail } from "@platform/api/types";
import { useRole } from "@platform/auth/RoleContext";
import { AuditTrail } from "@platform/components/AuditTrail";
import { StatusBadge } from "@platform/components/StatusBadge";
import { Button } from "@platform/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@platform/components/ui/card";
import { Input } from "@platform/components/ui/input";

import { EnabledPill } from "../components/EnabledPill";
import { asFlag, STATE_VARIANTS, TOOL_ID, type Flag } from "../tool";

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase text-muted-foreground">{label}</dt>
      <dd className="text-sm">{children}</dd>
    </div>
  );
}

function Control({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end gap-2 border-b pb-3 last:border-0 last:pb-0">
      <span className="w-40 text-sm font-medium">{label}</span>
      {children}
    </div>
  );
}

export function FlagDetailPage() {
  const { resourceId = "" } = useParams();
  const { role } = useRole();
  const [detail, setDetail] = useState<ResourceDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [prodReason, setProdReason] = useState("");
  const [rollout, setRollout] = useState("");
  const [rolloutReason, setRolloutReason] = useState("");
  const [archiveNote, setArchiveNote] = useState("");

  const load = useCallback(() => {
    getResource(TOOL_ID, resourceId, role)
      .then((d) => {
        setDetail(d);
        setError(null);
      })
      .catch((err) => setError(errorMessage(err)));
  }, [resourceId, role]);

  useEffect(load, [load]);

  async function run(action: string, input: Record<string, unknown>) {
    setBusy(true);
    setError(null);
    try {
      await invokeAction(TOOL_ID, resourceId, action, role, input);
      setProdReason("");
      setRolloutReason("");
      setArchiveNote("");
      load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  if (!detail) {
    return error ? (
      <p className="text-sm text-destructive">{error}</p>
    ) : (
      <p className="text-sm text-muted-foreground">Loading…</p>
    );
  }

  const flag: Flag = asFlag(detail.resource);
  const can = (name: string) => detail.available_actions.includes(`${TOOL_ID}.${name}`);
  const rolloutValue = rollout === "" ? String(flag.prod_rollout_pct) : rollout;
  const hasControls =
    can("activate") || can("set_staging") || can("set_production") || can("set_rollout") || can("archive");

  return (
    <div className="space-y-4">
      <Link to={`/${TOOL_ID}`} className="text-sm text-primary hover:underline">
        ← Back to flags
      </Link>
      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle className="font-mono text-base">{flag.key}</CardTitle>
          <StatusBadge state={flag.state} variants={STATE_VARIANTS} />
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">{flag.description}</p>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-3 md:grid-cols-3">
            <Field label="Flag id">{flag.id}</Field>
            <Field label="Owner team">{flag.owner_team}</Field>
            <Field label="Created">{flag.created_at}</Field>
            <Field label="Staging">
              <EnabledPill enabled={flag.staging_enabled} />
            </Field>
            <Field label="Production">
              <EnabledPill enabled={flag.prod_enabled} />
            </Field>
            <Field label="Production rollout">{flag.prod_rollout_pct}%</Field>
            <Field label="Last changed by">{flag.updated_by ?? "—"}</Field>
            <Field label="Change note">{flag.change_note ?? "—"}</Field>
          </dl>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Actions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {!hasControls && (
            <p className="text-sm text-muted-foreground">
              No actions available for your role in this state.
            </p>
          )}
          {can("activate") && (
            <Control label="Activate">
              <Button disabled={busy} onClick={() => void run("activate", {})}>
                Activate flag
              </Button>
            </Control>
          )}
          {can("set_staging") && (
            <Control label="Staging">
              <Button
                variant={flag.staging_enabled ? "outline" : "default"}
                disabled={busy}
                onClick={() => void run("set_staging", { enabled: !flag.staging_enabled })}
              >
                {flag.staging_enabled ? "Disable in staging" : "Enable in staging"}
              </Button>
            </Control>
          )}
          {can("set_production") && (
            <Control label="Production">
              <Input
                className="w-64"
                placeholder="Reason (required)"
                value={prodReason}
                onChange={(e) => setProdReason(e.target.value)}
              />
              <Button
                variant={flag.prod_enabled ? "outline" : "default"}
                disabled={busy}
                onClick={() =>
                  void run("set_production", { enabled: !flag.prod_enabled, reason: prodReason })
                }
              >
                {flag.prod_enabled ? "Disable in production" : "Enable in production"}
              </Button>
            </Control>
          )}
          {can("set_rollout") && (
            <Control label="Production rollout">
              <Input
                type="number"
                min={0}
                max={100}
                className="w-24"
                value={rolloutValue}
                onChange={(e) => setRollout(e.target.value)}
              />
              <Input
                className="w-64"
                placeholder="Reason (required)"
                value={rolloutReason}
                onChange={(e) => setRolloutReason(e.target.value)}
              />
              <Button
                disabled={busy}
                onClick={() =>
                  void run("set_rollout", {
                    percentage: Number(rolloutValue),
                    reason: rolloutReason,
                  })
                }
              >
                Update rollout
              </Button>
            </Control>
          )}
          {can("archive") && (
            <Control label="Archive">
              <Input
                className="w-64"
                placeholder="Note (required)"
                value={archiveNote}
                onChange={(e) => setArchiveNote(e.target.value)}
              />
              <Button
                variant="destructive"
                disabled={busy}
                onClick={() => void run("archive", { note: archiveNote })}
              >
                Archive flag
              </Button>
            </Control>
          )}
          {error && <p className="text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      <AuditTrail records={detail.audit} />
    </div>
  );
}
