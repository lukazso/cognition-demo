import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listResources } from "@platform/api/client";
import { errorMessage } from "@platform/api/types";
import { useRole } from "@platform/auth/RoleContext";
import { StatusBadge } from "@platform/components/StatusBadge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@platform/components/ui/card";
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

export function FlagListPage() {
  const { role } = useRole();
  const [flags, setFlags] = useState<Flag[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listResources(TOOL_ID, role)
      .then((page) => {
        setFlags(page.items.map(asFlag));
        setError(null);
      })
      .catch((err) => setError(errorMessage(err)));
  }, [role]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{TITLE}</CardTitle>
        <CardDescription>{DESCRIPTION}</CardDescription>
      </CardHeader>
      <CardContent>
        {error ? (
          <p className="text-sm text-destructive">{error}</p>
        ) : (
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
