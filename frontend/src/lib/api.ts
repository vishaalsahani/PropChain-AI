export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("propchain_token");
}

export function setToken(token: string) {
  localStorage.setItem("propchain_token", token);
}

export function clearToken() {
  localStorage.removeItem("propchain_token");
}

export function getUserEmail(): string | null {
  const token = getToken();
  if (!token) return null;
  try {
    const payload = token.split(".")[1];
    if (!payload) return null;
    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), "=");
    const claims = JSON.parse(atob(padded));
    return typeof claims.sub === "string" ? claims.sub : null;
  } catch {
    return null;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers || {});
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const raw = await res.text();
    let detail = raw;
    try {
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed.detail === "string") detail = parsed.detail;
    } catch {
      // Not JSON — use the raw body as the message.
    }
    throw new Error(detail || `Request failed: ${res.status}`);
  }
  if (res.headers.get("content-type")?.includes("application/json")) {
    return res.json();
  }
  return res as unknown as T;
}

export const api = {
  health: () => request<{ status: string; components: Record<string, string> }>("/health"),
  me: () => request<UserOut>("/auth/me"),
  register: (body: { email: string; full_name: string; password: string }) =>
    request("/auth/register", { method: "POST", body: JSON.stringify(body) }),
  login: async (email: string, password: string) => {
    const body = new URLSearchParams({ username: email, password });
    const res = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    if (!res.ok) throw new Error("Login failed");
    return res.json() as Promise<{ access_token: string }>;
  },
  listProperties: () => request<Property[]>("/properties"),
  createProperty: (body: PropertyInput) => request<Property>("/properties", { method: "POST", body: JSON.stringify(body) }),
  getProperty: (id: number) => request<Property>(`/properties/${id}`),
  uploadDocument: (propertyId: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<DocumentItem>(`/documents/upload/${propertyId}`, { method: "POST", body: form });
  },
  listDocuments: (propertyId: number) => request<DocumentItem[]>(`/documents/property/${propertyId}`),
  runAnalysis: (propertyId: number) => request<AnalysisResult>(`/analysis/run/${propertyId}`, { method: "POST" }),
  getFindings: (propertyId: number) => request<Finding[]>(`/analysis/${propertyId}/findings`),
  getOwnership: (propertyId: number) => request<OwnershipNode[]>(`/analysis/${propertyId}/ownership`),
  getVerdict: (propertyId: number) => request<VerdictOut>(`/analysis/${propertyId}/verdict`),
  registerBlockchain: (documentId: number) =>
    request<BlockchainResult>(`/blockchain/register/${documentId}`, { method: "POST" }),
  verifyBlockchain: (documentId: number) =>
    request<BlockchainResult>(`/blockchain/verify/${documentId}`, { method: "POST" }),
  blockchainStatus: () => request<BlockchainStatus>("/blockchain/status"),
  downloadReport: (propertyId: number) => `${API_URL}/reports/${propertyId}/pdf`,

  listRulePacks: () => request<RulePackSummary[]>("/rule-packs"),
  getRulePack: (jurisdiction: string) =>
    request<RulePack>(`/rule-packs/${encodeURIComponent(jurisdiction)}`),
  adminListRulePacks: () => request<RulePackSummary[]>("/admin/rule-packs"),
  adminGetRulePack: (jurisdiction: string) =>
    request<RulePack>(`/admin/rule-packs/${encodeURIComponent(jurisdiction)}`),
  adminGetRule: (jurisdiction: string, ruleCode: string) =>
    request<RuleDetail>(
      `/admin/rule-packs/${encodeURIComponent(jurisdiction)}/rules/${encodeURIComponent(ruleCode)}`
    ),
  adminUpdateRule: (jurisdiction: string, ruleCode: string, body: RuleUpdateInput) =>
    request<RuleDetail>(
      `/admin/rule-packs/${encodeURIComponent(jurisdiction)}/rules/${encodeURIComponent(ruleCode)}`,
      { method: "PATCH", body: JSON.stringify(body) }
    ),
  adminCreateRule: (jurisdiction: string, body: RuleCreateInput) =>
    request<LegalRule>(`/admin/rule-packs/${encodeURIComponent(jurisdiction)}/rules`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  adminRollbackRule: (
    jurisdiction: string,
    ruleCode: string,
    body: { version: number; change_note?: string | null }
  ) =>
    request<RuleDetail>(
      `/admin/rule-packs/${encodeURIComponent(jurisdiction)}/rules/${encodeURIComponent(
        ruleCode
      )}/rollback`,
      { method: "POST", body: JSON.stringify(body) }
    ),
  adminResetRulePack: (
    jurisdiction: string,
    body: { change_note?: string | null } = {}
  ) =>
    request<RulePack>(`/admin/rule-packs/${encodeURIComponent(jurisdiction)}/reset`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  listRuns: (propertyId: number) => request<AnalysisRunSummary[]>(`/analysis/${propertyId}/runs`),
  reviewQueue: () => request<ReviewQueueItem[]>("/review/queue"),
  reviewRun: (
    runId: number,
    body: {
      decision: "confirmed" | "overridden";
      verdict?: "verified" | "needs_review" | "flagged" | null;
      note: string;
    }
  ) =>
    request<AnalysisRunSummary>(`/review/runs/${runId}/decision`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  reviewFinding: (
    findingId: number,
    body: {
      status: "open" | "confirmed" | "dismissed" | "needs_evidence";
      note?: string | null;
      expected_status?: string | null;
    }
  ) =>
    request<Finding>(`/review/findings/${findingId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
};

export type PropertyInput = {
  title: string;
  state?: string;
  district?: string;
  taluka?: string;
  village?: string;
  survey_number?: string;
  gat_number?: string;
  cts_number?: string;
  area_sqft?: number;
};

export type Property = PropertyInput & {
  id: number;
  status: string;
  risk_score: number | null;
  created_at: string;
};

export type DocumentItem = {
  id: number;
  property_id: number;
  filename: string;
  file_hash: string;
  doc_type: string;
  status: string;
  extracted_data: string | null;
  blockchain_tx: string | null;
  blockchain_verified: boolean | null;
  created_at: string;
};

export type Finding = {
  id: number;
  category: string;
  title: string;
  description: string;
  severity: "low" | "medium" | "high" | "critical";
  confidence: number;
  evidence: string | null;
  rule_ref: string | null;
  status: FindingReviewStatus;
  reviewed_by?: number | null;
  reviewed_at?: string | null;
  review_note?: string | null;
};

export type OwnershipNode = {
  id: number;
  person_name: string;
  transaction_type: string;
  transaction_date: string;
  document_ref: string | null;
  sequence: number;
  from_party?: string | null;
  gap_flag?: boolean;
};

export type VerdictReasons = {
  verdict?: string;
  reasons?: string[];
  not_checked?: string[];
};

export type VerdictOut = {
  property_id: number;
  analysis_run_id: number | null;
  verdict: "verified" | "needs_review" | "flagged" | null;
  reasons: string[];
  not_checked: string[];
  risk_score: number | null;
  engine_version: string | null;
  review_status?: string;
  review_verdict?: string | null;
  review_note?: string | null;
  reviewed_at?: string | null;
};

export type AnalysisResult = {
  property_id: number;
  findings: Finding[];
  ownership_chain: OwnershipNode[];
  risk_score: number;
  summary: string;
  verdict: string | null;
  verdict_reasons: VerdictReasons | null;
};

export type BlockchainResult = {
  document_id: number;
  file_hash: string;
  status: string;
  blockchain_tx: string | null;
  message: string;
  mode?: string | null;
  network?: string | null;
  chain_id?: number | null;
  contract_address?: string | null;
  block_number?: number | null;
};

export type BlockchainStatus = {
  mode: "mock" | "evm";
  connected: boolean;
  network: string | null;
  chain_id: number | null;
  contract_address: string | null;
  account: string | null;
  message: string;
};

export type UserRole = "buyer" | "owner" | "reviewer" | "admin";

export type UserOut = {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
};

export type LegalRule = {
  id: number;
  rule_code: string;
  jurisdiction: string;
  law_name: string | null;
  section: string | null;
  title: string;
  description: string | null;
  category: string | null;
  severity: Finding["severity"];
  confidence: number;
  conditions: Record<string, unknown> | null;
  evidence_required: unknown;
  recommended_action: string | null;
  source_url: string | null;
  effective_from: string | null;
  effective_to: string | null;
  is_active: boolean;
  current_version: number;
  is_evaluable: boolean;
  created_at: string;
};

export type RuleVersion = {
  version: number;
  snapshot: Record<string, unknown> | null;
  change_note: string | null;
  created_by: number | null;
  created_at: string;
};

export type RuleDetail = LegalRule & { versions: RuleVersion[] };

export type RulePackSummary = {
  jurisdiction: string;
  code: string;
  name: string;
  version: number;
  rule_count: number;
  active_rule_count: number;
  evaluable_rule_count: number;
  signature: string;
  updated_at: string | null;
};

export type RulePack = RulePackSummary & { rules: LegalRule[] };

export type RuleUpdateInput = {
  title?: string;
  description?: string | null;
  category?: string;
  severity?: Finding["severity"];
  confidence?: number;
  conditions?: Record<string, unknown> | null;
  evidence_required?: unknown;
  recommended_action?: string | null;
  law_name?: string | null;
  section?: string | null;
  source_url?: string | null;
  effective_from?: string | null;
  effective_to?: string | null;
  is_active?: boolean;
  change_note?: string | null;
  expected_version?: number;
};

export type RuleCreateInput = Omit<RuleUpdateInput, "expected_version"> & {
  rule_code: string;
  title: string;
};

export type FindingReviewStatus = "open" | "confirmed" | "dismissed" | "needs_evidence";

export type AnalysisRunSummary = {
  id: number;
  property_id: number;
  status: string;
  engine_version: string;
  verdict: "verified" | "needs_review" | "flagged" | null;
  risk_score: number | null;
  summary: string | null;
  started_at: string;
  finished_at: string | null;
  created_by: number | null;
  review_status: string;
  review_verdict: "verified" | "needs_review" | "flagged" | null;
  reviewed_by: number | null;
  reviewed_at: string | null;
  review_note: string | null;
  finding_count: number;
};

export type ReviewQueueItem = {
  property_id: number;
  title: string;
  village: string;
  district: string;
  run_id: number;
  verdict: "verified" | "needs_review" | "flagged" | null;
  risk_score: number | null;
  review_status: string;
  review_verdict: "verified" | "needs_review" | "flagged" | null;
  open_findings: number;
  total_findings: number;
  finished_at: string | null;
};
