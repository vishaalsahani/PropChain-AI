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

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers || {});
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Request failed: ${res.status}`);
  }
  if (res.headers.get("content-type")?.includes("application/json")) {
    return res.json();
  }
  return res as unknown as T;
}

export const api = {
  health: () => request<{ status: string; components: Record<string, string> }>("/health"),
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
  registerBlockchain: (documentId: number) =>
    request<BlockchainResult>(`/blockchain/register/${documentId}`, { method: "POST" }),
  verifyBlockchain: (documentId: number) =>
    request<BlockchainResult>(`/blockchain/verify/${documentId}`, { method: "POST" }),
  downloadReport: (propertyId: number) => `${API_URL}/reports/${propertyId}/pdf`,
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
  status: string;
};

export type OwnershipNode = {
  id: number;
  person_name: string;
  transaction_type: string;
  transaction_date: string;
  document_ref: string | null;
  sequence: number;
};

export type AnalysisResult = {
  property_id: number;
  findings: Finding[];
  ownership_chain: OwnershipNode[];
  risk_score: number;
  summary: string;
};

export type BlockchainResult = {
  document_id: number;
  file_hash: string;
  status: string;
  blockchain_tx: string | null;
  message: string;
};
