import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { RoleProvider } from "@platform/auth/RoleContext";
import { RoleSwitcher } from "@platform/components/RoleSwitcher";
import "@platform/theme.css";

import { FlagDetailPage } from "./pages/FlagDetailPage";
import { FlagListPage } from "./pages/FlagListPage";
import { TITLE, TOOL_ID } from "./tool";

function App() {
  return (
    <RoleProvider>
      <div className="min-h-screen">
        <header className="border-b bg-card">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
            <div className="flex items-center gap-6">
              <span className="font-semibold">Internal Tools</span>
              <span className="rounded-md bg-secondary px-3 py-1.5 text-sm font-medium">{TITLE}</span>
            </div>
            <RoleSwitcher />
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-6 py-6">
          <Routes>
            <Route path={`/${TOOL_ID}`} element={<FlagListPage />} />
            <Route path={`/${TOOL_ID}/:resourceId`} element={<FlagDetailPage />} />
            <Route path="*" element={<Navigate to={`/${TOOL_ID}`} replace />} />
          </Routes>
        </main>
      </div>
    </RoleProvider>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
