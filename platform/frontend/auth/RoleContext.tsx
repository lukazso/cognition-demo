import { createContext, useContext, useState, type ReactNode } from "react";

import type { Role } from "../api/types";

interface RoleContextValue {
  role: Role;
  setRole: (role: Role) => void;
}

const RoleContext = createContext<RoleContextValue>({ role: "viewer", setRole: () => {} });

export function RoleProvider({ children }: { children: ReactNode }) {
  const [role, setRole] = useState<Role>("operator");
  return <RoleContext.Provider value={{ role, setRole }}>{children}</RoleContext.Provider>;
}

export function useRole() {
  return useContext(RoleContext);
}
