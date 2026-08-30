import type { Role } from "../api/types";
import { useRole } from "../auth/RoleContext";
import { Button } from "./ui/button";

const ROLES: Role[] = ["viewer", "operator", "supervisor"];

export function RoleSwitcher() {
  const { role, setRole } = useRole();
  return (
    <div className="flex items-center gap-1 rounded-lg border bg-muted/40 p-1">
      {ROLES.map((r) => (
        <Button
          key={r}
          size="sm"
          variant={r === role ? "default" : "ghost"}
          onClick={() => setRole(r)}
          className="capitalize"
        >
          {r}
        </Button>
      ))}
    </div>
  );
}
