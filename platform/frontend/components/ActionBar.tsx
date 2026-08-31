import { useState } from "react";

import { errorMessage } from "../api/types";
import type { ActionDef } from "../tool";
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";

interface ActionBarProps {
  actions: ActionDef[];
  availableActions: string[];
  onInvoke: (name: string, input: Record<string, unknown>) => Promise<void>;
}

export function ActionBar({ actions, availableActions, onInvoke }: ActionBarProps) {
  const [open, setOpen] = useState<ActionDef | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const visible = actions.filter((a) => availableActions.some((n) => n === a.name || n.endsWith(`.${a.name}`)));

  async function invoke(action: ActionDef, input: Record<string, unknown>) {
    setBusy(true);
    setError(null);
    try {
      await onInvoke(action.name, input);
      setOpen(null);
      setValues({});
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {visible.length === 0 && (
          <p className="text-sm text-muted-foreground">No actions available for your role in this state.</p>
        )}
        {visible.map((action) => (
          <Button
            key={action.name}
            variant={action.variant ?? "default"}
            disabled={busy}
            onClick={() => {
              if (action.fields?.length) {
                setOpen(open?.name === action.name ? null : action);
                setValues({});
                setError(null);
              } else {
                void invoke(action, {});
              }
            }}
          >
            {action.label}
          </Button>
        ))}
      </div>
      {open && (
        <Card>
          <CardContent className="space-y-3 pt-6">
            {open.fields?.map((field) => (
              <div key={field.key} className="space-y-1">
                <label className="text-sm font-medium">{field.label}</label>
                {field.kind === "textarea" ? (
                  <Textarea
                    placeholder={field.placeholder}
                    value={values[field.key] ?? ""}
                    onChange={(e) => setValues({ ...values, [field.key]: e.target.value })}
                  />
                ) : (
                  <Input
                    placeholder={field.placeholder}
                    value={values[field.key] ?? ""}
                    onChange={(e) => setValues({ ...values, [field.key]: e.target.value })}
                  />
                )}
              </div>
            ))}
            <div className="flex gap-2">
              <Button disabled={busy} onClick={() => void invoke(open, values)}>
                Confirm {open.label.toLowerCase()}
              </Button>
              <Button variant="ghost" onClick={() => setOpen(null)}>
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  );
}
