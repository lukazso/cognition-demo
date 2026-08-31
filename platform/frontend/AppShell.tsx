import { Link, Route, Routes, useLocation } from "react-router-dom";

import { RoleProvider } from "./auth/RoleContext";
import { RoleSwitcher } from "./components/RoleSwitcher";
import { DetailPage } from "./pages/DetailPage";
import { QueuePage } from "./pages/QueuePage";
import type { ToolFrontendConfig } from "./tool";
import { cn } from "./lib/utils";

export function AppShell({ tools }: { tools: ToolFrontendConfig[] }) {
  const location = useLocation();
  return (
    <RoleProvider>
      <div className="min-h-screen">
        <header className="border-b bg-card">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
            <div className="flex items-center gap-6">
              <span className="font-semibold">Internal Tools</span>
              <nav className="flex items-center gap-1">
                {tools.map((tool) => (
                  <Link
                    key={tool.toolId}
                    to={`/${tool.toolId}`}
                    className={cn(
                      "rounded-md px-3 py-1.5 text-sm transition-colors hover:bg-accent",
                      location.pathname.startsWith(`/${tool.toolId}`)
                        ? "bg-secondary font-medium"
                        : "text-muted-foreground",
                    )}
                  >
                    {tool.title}
                  </Link>
                ))}
              </nav>
            </div>
            <RoleSwitcher />
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-6 py-6">
          <Routes>
            {tools.map((tool) => (
              <Route key={tool.toolId} path={`/${tool.toolId}`} element={<QueuePage config={tool} />} />
            ))}
            {tools.map((tool) => (
              <Route
                key={`${tool.toolId}-detail`}
                path={`/${tool.toolId}/:resourceId`}
                element={<DetailPage config={tool} />}
              />
            ))}
            <Route path="*" element={tools[0] ? <QueuePage config={tools[0]} /> : null} />
          </Routes>
        </main>
      </div>
    </RoleProvider>
  );
}
