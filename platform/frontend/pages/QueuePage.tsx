import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listResources } from "../api/client";
import { errorMessage } from "../api/types";
import { useRole } from "../auth/RoleContext";
import { StatusBadge } from "../components/StatusBadge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import type { ToolFrontendConfig } from "../tool";

export function QueuePage({ config }: { config: ToolFrontendConfig }) {
  const { role } = useRole();
  const [items, setItems] = useState<Record<string, unknown>[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listResources(config.toolId, role)
      .then((page) => {
        setItems(page.items);
        setError(null);
      })
      .catch((err) => setError(errorMessage(err)));
  }, [config.toolId, role]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{config.title}</CardTitle>
        <CardDescription>{config.description}</CardDescription>
      </CardHeader>
      <CardContent>
        {error ? (
          <p className="text-sm text-destructive">{error}</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                {config.columns.map((c) => (
                  <TableHead key={c.key}>{c.label}</TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((item) => {
                const id = String(item[config.resourceIdKey]);
                return (
                  <TableRow key={id}>
                    {config.columns.map((c) => (
                      <TableCell key={c.key}>
                        {c.key === config.resourceIdKey ? (
                          <Link to={`/${config.toolId}/${id}`} className="font-medium text-primary hover:underline">
                            {id}
                          </Link>
                        ) : c.key === config.statusKey ? (
                          <StatusBadge state={String(item[c.key])} variants={config.statusVariants} />
                        ) : (
                          String(item[c.key] ?? "")
                        )}
                      </TableCell>
                    ))}
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
