import type { ToolFrontendConfig } from "@platform/tool";

export const kycTool: ToolFrontendConfig = {
  toolId: "kyc",
  title: "KYC Review",
  description: "Review, escalate, approve, or reject customer KYC cases.",
  resourceIdKey: "id",
  columns: [
    { key: "id", label: "Case" },
    { key: "applicant_name", label: "Applicant" },
    { key: "country", label: "Country" },
    { key: "risk_score", label: "Risk" },
    { key: "state", label: "State" },
    { key: "submitted_at", label: "Submitted" },
  ],
  detailFields: [
    { key: "applicant_name", label: "Applicant" },
    { key: "email", label: "Email" },
    { key: "country", label: "Country" },
    { key: "risk_score", label: "Risk score" },
    { key: "submitted_at", label: "Submitted" },
    { key: "reviewer_id", label: "Reviewer" },
    { key: "resolution_note", label: "Resolution note" },
  ],
  statusKey: "state",
  statusVariants: {
    pending: "secondary",
    in_review: "info",
    escalated: "warning",
    approved: "success",
    rejected: "destructive",
  },
  actions: [
    { name: "start_review", label: "Start review" },
    {
      name: "escalate",
      label: "Escalate",
      variant: "outline",
      fields: [
        { key: "reason", label: "Reason", kind: "textarea", required: true, placeholder: "Why is this being escalated?" },
      ],
    },
    {
      name: "approve",
      label: "Approve",
      fields: [{ key: "note", label: "Note (optional)", kind: "text" }],
    },
    {
      name: "reject",
      label: "Reject",
      variant: "destructive",
      fields: [
        { key: "reason", label: "Reason", kind: "textarea", required: true, placeholder: "Why is this being rejected?" },
      ],
    },
  ],
};
