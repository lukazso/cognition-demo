import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import { AppShell } from "@platform/AppShell";
import "@platform/theme.css";

import { kycTool } from "./tool";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AppShell tools={[kycTool]} />
    </BrowserRouter>
  </React.StrictMode>,
);
