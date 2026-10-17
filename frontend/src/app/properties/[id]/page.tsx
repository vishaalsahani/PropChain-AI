"use client";

import { use, useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import DocumentUploader, { DocumentList } from "@/components/DocumentUploader";
import FindingsList from "@/components/FindingsList";
import OwnershipTimeline from "@/components/OwnershipTimeline";
import RiskIndicator from "@/components/RiskIndicator";
import VerdictBadge from "@/components/VerdictBadge";
import { api, DocumentItem, Finding, OwnershipNode, Property, VerdictOut, getToken } from "@/lib/api";

export default function PropertyDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const propertyId = Number(id);
  const [property, setProperty] = useState<Property | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [ownership, setOwnership] = useState<OwnershipNode[]>([]);
  const [verdict, setVerdict] = useState<VerdictOut | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function refresh() {
    const [prop, docs, findingList, chain] = await Promise.all([
      api.getProperty(propertyId),
      api.listDocuments(propertyId),
      api.getFindings(propertyId),
      api.getOwnership(propertyId),
    ]);
    setProperty(prop);
    setDocuments(docs);
    setFindings(findingList);
    setOwnership(chain);
    // 404 until the first analysis run exists; that is a normal state.
    setVerdict(await api.getVerdict(propertyId).catch(() => null));
  }

  useEffect(() => {
    if (!getToken()) {
      window.location.href = "/login";
      return;
    }
    refresh().catch(() => setError("Unable to load property"));
  }, [propertyId]);

  async function runAnalysis() {
    setMessage("Running analysis...");
    const result = await api.runAnalysis(propertyId);
    setFindings(result.findings);
    setOwnership(result.ownership_chain);
    setMessage(result.summary);
    await refresh();
  }

  async function downloadReport() {
    const token = getToken();
    if (!token) return;
    const res = await fetch(api.downloadReport(propertyId), {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `propchain-report-${propertyId}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (!property) {
    return (
      <>
        <Navbar />
        <main className="mx-auto max-w-6xl px-4 py-8">{error || "Loading..."}</main>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-6xl space-y-6 px-4 py-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">{property.title}</h1>
            <p className="text-sm text-slate-500">
              {property.village}, {property.taluka}, {property.district}, {property.state}
            </p>
            <p className="text-sm text-slate-500">
              Survey {property.survey_number || "-"} · Gat {property.gat_number || "-"} · Status {property.status}
            </p>
          </div>
          <div className="flex gap-2">
            <button className="btn-primary" onClick={runAnalysis}>
              Run Analysis
            </button>
            <button className="btn-secondary" onClick={downloadReport}>
              Download Report
            </button>
          </div>
        </div>

        {message && <p className="text-sm text-brand-700">{message}</p>}

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
            <DocumentUploader propertyId={propertyId} onUploaded={refresh} />
            <div className="card">
              <h2 className="mb-4 text-lg font-semibold">Documents</h2>
              <DocumentList documents={documents} onAction={refresh} />
            </div>
            <div className="card">
              <h2 className="mb-4 text-lg font-semibold">Findings</h2>
              <FindingsList findings={findings} />
            </div>
          </div>
          <div className="space-y-6">
            <VerdictBadge verdict={verdict} />
            <RiskIndicator score={property.risk_score} />
            <div className="card">
              <h2 className="mb-4 text-lg font-semibold">Ownership Chain</h2>
              <OwnershipTimeline nodes={ownership} />
            </div>
          </div>
        </div>

        <div className="card text-xs text-slate-500">
          Disclaimer: PropChain-AI provides AI-assisted documentary analysis and risk indicators only.
          It does not establish legal title or replace government records and professional legal advice.
        </div>
      </main>
    </>
  );
}
