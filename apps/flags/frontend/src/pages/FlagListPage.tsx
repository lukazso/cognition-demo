import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { invokeCreateAction, listResources } from "@platform/api/client";
import { errorMessage } from "@platform/api/types";
import { useRole } from "@platform/auth/RoleContext";
import { StatusBadge } from "@platform/components/StatusBadge";
import { Button } from "@platform/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@platform/components/ui/card";
import { Input } from "@platform/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@platform/components/ui/table";

import { EnabledPill } from "../components/EnabledPill";
import { asFlag, DESCRIPTION, STATE_VARIANTS, TITLE, TOOL_ID, type Flag } from "../tool";

const EMPTY_DRAFT = { key: "", description: "", owner_team: "" };

export function FlagListPage() {
  const { role } = useRole();
  const navigate = useNavigate();
  const [flags, setFlags] = useState<Flag[]>([]);
  const [canCreate, setCanCreate] = useState(false);
  const [draft, setDraft] = useState<typeof EMPTY_DRAFT | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listResources(TOOL_ID, role)
      .then((page) => {
        setFlags(page.items.map(asFlag));
        setCanCreate(page.available_create_actions.includes(`${TOOL_ID}.create`));
        setError(null);
      })
      .catch((err) => setError(errorMessage(err)));
  }, [role]);

  async function create(input: typeof EMPTY_DRAFT) {
    setBusy(true);
    setError(null);
    try {
      const created = await invokeCreateAction(TOOL_ID, "create", role, input);
      navigate(`/${TOOL_ID}/${created.resource_id}`);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardHeader className="flex-row items-start justify-between space-y-0">
        <div className="space-y-1.5">
          <CardTitle>{TITLE}</CardTitle>
          <CardDescription>{DESCRIPTION}</CardDescription>
        </div>
        {canCreate && (
          <Button variant={draft ? "ghost" : "default"} onClick={() => setDraft(draft ? null : EMPTY_DRAFT)}>
            {draft ? "Cancel" : "New flag"}
          </Button>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        {draft && (
          <div className="flex flex-wrap items-end gap-2 rounded-lg border p-3">
            <Input
              className="w-64"
              placeholder="Key, e.g. checkout.new-flow"
              value={draft.key}
              onChange={(e) => setDraft({ ...draft, key: e.target.value })}
            />
            <Input
              className="w-72"
              placeholder="Description"
              value={draft.description}
              onChange={(e) => setDraft({ ...draft, description: e.target.value })}
            />
            <Input
              className="w-40"
              placeholder="Owner team"
              value={draft.owner_team}
              onChange={(e) => setDraft({ ...draft, owner_team: e.target.value })}
            />
            <Button disabled={busy} onClick={() => void create(draft)}>
              Create flag
            </Button>
          </div>
        )}
        {error && <p className="text-sm text-destructive">{error}</p>}
        {error && flags.length === 0 ? null : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Key</TableHead>
                <TableHead>Owner team</TableHead>
                <TableHead>State</TableHead>
                <TableHead>Staging</TableHead>
                <TableHead>Production</TableHead>
                <TableHead>Rollout</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {flags.map((flag) => (
                <TableRow key={flag.id}>
                  <TableCell>
                    <Link
                      to={`/${TOOL_ID}/${flag.id}`}
                      className="font-medium text-primary hover:underline"
                    >
                      {flag.key}
                    </Link>
                  </TableCell>
                  <TableCell>{flag.owner_team}</TableCell>
                  <TableCell>
                    <StatusBadge state={flag.state} variants={STATE_VARIANTS} />
                  </TableCell>
                  <TableCell>
                    <EnabledPill enabled={flag.staging_enabled} />
                  </TableCell>
                  <TableCell>
                    <EnabledPill enabled={flag.prod_enabled} />
                  </TableCell>
                  <TableCell>{flag.prod_enabled ? `${flag.prod_rollout_pct}%` : "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
