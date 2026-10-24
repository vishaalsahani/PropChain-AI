"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import DocumentUploader, { DocumentList } from "@/components/DocumentUploader";
import FindingsList from "@/components/FindingsList";
import OwnershipTimeline from "@/components/OwnershipTimeline";
import RiskIndicator from "@/components/RiskIndicator";
import VerdictBadge from "@/components/VerdictBadge";
import {
  AlertTriangle,
  ArrowLeft,
  Calendar,
  Download,
  Hash,
  Info,
  MapPin,
  Ruler,
  Sparkles,
  Spinner,
  X,
} from "@/components/icons";
import {
  api,
  DocumentItem,
  Finding,
  OwnershipNode,
  Property,
  VerdictOut,
  getToken,
} from "@/lib/api";
import { formatArea, formatDate, propertyStatus } from "@/lib/presentation";

type Notice = { text: string; tone: "success" | "warning" | "danger" | "info" };

const NOTICE_STYLES: Record<Notice["tone"], string> = {
  success: "border-emerald-200 bg-emerald-50/80 text-emerald-800",
  warning: "border-amber-200 bg-amber-50/80 text-amber-800",
  danger: "border-rose-200 bg-rose-50/80 text-rose-800",
  info: "border-brand-200 bg-brand-50/80 text-brand-900",
};

export default function PropertyDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const propertyId = Number(id);
  const [property, setProperty] = useState<Property | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [ownership, setOwnership] = useState<OwnershipNode[]>([]);
  const [verdict, setVerdict] = useState<VerdictOut | null>(null);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [loading, setLoading] = useState(true);

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
    refresh()
      .catch(() => setError("Unable to load this property file. Check that the API is running."))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [propertyId]);

  async function runAnalysis() {
    setRunning(true);
    setError("");
    setNotice(null);
    try {
      const result = await api.runAnalysis(propertyId);
      setFindings(result.findings);
      setOwnership(result.ownership_chain);
      const tone: Notice["tone"] =
        result.verdict === "verified" ? "success" : result.verdict === "flagged" ? "danger" : "warning";
      setNotice({ text: result.summary, tone });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "The analysis could not be completed.");
    } finally {
      setRunning(false);
    }
  }

  async function downloadReport() {
    const token = getToken();
    if (!token) return;
    setDownloading(true);
    try {
      const res = await fetch(api.downloadReport(propertyId), {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Report unavailable");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `propchain-report-${propertyId}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError("The report could not be generated yet. Run the analysis first.");
    } finally {
      setDownloading(false);
    }
  }

  if (loading && !property) {
    return (
      <>
        <Navbar />
        <main className="shell space-y-6 py-8">
          <div className="skeleton h-3 w-40" />
          <div className="space-y-3">
            <div className="skeleton h-3 w-24" />
            <div className="skeleton h-9 w-2/3 max-w-lg" />
            <div className="skeleton h-3 w-1/3" />
          </div>
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="space-y-6 lg:col-span-2">
              <div className="skeleton h-44 w-full" />
              <div className="skeleton h-64 w-full" />
              <div className="skeleton h-52 w-full" />
            </div>
            <div className="space-y-6">
              <div className="skeleton h-40 w-full" />
              <div className="skeleton h-64 w-full" />
            </div>
          </div>
        </main>
      </>
    );
  }

  if (!property) {
    return (
      <>
        <Navbar />
        <main className="shell py-16">
          <div className="mx-auto max-w-md rounded-2xl border border-rose-200 bg-rose-50 p-8 text-center">
            <AlertTriangle className="mx-auto h-8 w-8 text-rose-500" />
            <h1 className="mt-4 text-xl font-medium">This file could not be opened</h1>
            <p className="mt-2 text-sm text-rose-700">{error || "The property was not found."}</p>
            <Link href="/dashboard" className="btn-secondary mt-6 bg-white/70">
              <ArrowLeft className="h-4 w-4" />
              Back to portfolio
            </Link>
          </div>
        </main>
      </>
    );
  }

  const status = propertyStatus(property.status);
  const location = [property.village, property.taluka, property.district, property.state]
    .filter((part, index, parts) => Boolean(part) && parts.indexOf(part) === index)
    .join(", ");

  return (
    <>
      <Navbar />
      <main className="shell space-y-7 py-8 sm:py-10">
        <div className="animate-fade-up">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 transition hover:text-brand-700"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Portfolio
          </Link>

          <div className="mt-5 flex flex-wrap items-start justify-between gap-5">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2.5">
                <span className={status.badge}>
                  <span className={`h-1.5 w-1.5 rounded-full ${status.dot}`} />
                  {status.label}
                </span>
                <span className="inline-flex items-center gap-1.5 text-[11px] text-slate-400">
                  <Calendar className="h-3.5 w-3.5" />
                  Created {formatDate(property.created_at)}
                </span>
              </div>
              <h1 className="mt-3 text-balance text-[30px] font-medium leading-tight sm:text-[36px]">
                {property.title}
              </h1>
              <p className="mt-2 flex items-center gap-1.5 text-sm text-slate-500">
                <MapPin className="h-4 w-4 shrink-0 text-slate-400" />
                {location || "Location not set"}
              </p>
              <div className="mt-4 flex flex-wrap gap-1.5">
                <span className="chip">
                  <Hash className="h-3.5 w-3.5 text-slate-400" />
                  Survey {property.survey_number || "—"}
                </span>
                <span className="chip">
                  <Hash className="h-3.5 w-3.5 text-slate-400" />
                  Gat {property.gat_number || "—"}
                </span>
                <span className="chip">
                  <Ruler className="h-3.5 w-3.5 text-slate-400" />
                  {formatArea(property.area_sqft)}
                </span>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <button className="btn-primary" onClick={runAnalysis} disabled={running} aria-busy={running}>
                {running ? <Spinner /> : <Sparkles className="h-4 w-4" />}
                {running ? "Running analysis…" : "Run analysis"}
              </button>
              <button className="btn-secondary" onClick={downloadReport} disabled={downloading}>
                {downloading ? <Spinner /> : <Download className="h-4 w-4" />}
                {downloading ? "Preparing…" : "Report"}
              </button>
            </div>
          </div>
        </div>

        {notice && (
          <div
            role="status"
            className={`animate-fade-in flex items-start gap-3 rounded-2xl border px-4 py-3.5 text-sm ${NOTICE_STYLES[notice.tone]}`}
          >
            {notice.tone === "success" ? (
              <Sparkles className="mt-0.5 h-4 w-4 shrink-0" />
            ) : (
              <Info className="mt-0.5 h-4 w-4 shrink-0" />
            )}
            <p className="flex-1 leading-relaxed">{notice.text}</p>
            <button
              onClick={() => setNotice(null)}
              className="rounded-lg p-1 transition hover:bg-black/5"
              aria-label="Dismiss message"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {error && (
          <div
            role="alert"
            className="flex items-start gap-3 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3.5 text-sm text-rose-700"
          >
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <p className="flex-1">{error}</p>
            <button
              onClick={() => setError("")}
              className="rounded-lg p-1 transition hover:bg-black/5"
              aria-label="Dismiss error"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="animate-fade-up animation-delay-100 space-y-6 lg:col-span-2">
            <DocumentUploader propertyId={propertyId} onUploaded={refresh} />

            <section className="card">
              <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h2 className="text-base font-semibold">Documents</h2>
                  <p className="mt-0.5 text-xs text-slate-400">
                    {documents.length} {documents.length === 1 ? "file" : "files"} in the off-chain store
                  </p>
                </div>
                <span className="badge bg-slate-50 text-slate-600 ring-1 ring-inset ring-slate-500/15">
                  {documents.filter((doc) => doc.status === "completed").length} processed
                </span>
              </div>
              <DocumentList documents={documents} onAction={refresh} />
            </section>

            <section className="card">
              <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h2 className="text-base font-semibold">Findings</h2>
                  <p className="mt-0.5 text-xs text-slate-400">
                    Inconsistencies raised by the matrix and the Maharashtra rule pack
                  </p>
                </div>
                {findings.length > 0 && (
                  <span className="badge bg-brand-50 text-brand-800 ring-1 ring-inset ring-brand-600/15">
                    {findings.length} {findings.length === 1 ? "finding" : "findings"}
                  </span>
                )}
              </div>
              <FindingsList findings={findings} hasRun={Boolean(verdict)} />
            </section>
          </div>

          <aside className="animate-fade-up animation-delay-200 space-y-6">
            <VerdictBadge verdict={verdict} />
            <RiskIndicator score={property.risk_score} />

            <section className="card">
              <div className="mb-4 flex items-center justify-between gap-2">
                <h2 className="text-base font-semibold">Ownership chain</h2>
                {ownership.length > 0 && (
                  <span className="badge bg-slate-50 text-slate-600 ring-1 ring-inset ring-slate-500/15">
                    {ownership.length} {ownership.length === 1 ? "step" : "steps"}
                  </span>
                )}
              </div>
              <OwnershipTimeline nodes={ownership} />
            </section>
          </aside>
        </div>

        <div className="animate-fade-in flex items-start gap-3 rounded-2xl border border-ink/[0.06] bg-white/50 px-5 py-4">
          <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-brand-50 text-brand-700">
            <Info className="h-4 w-4" />
          </span>
          <p className="text-[11px] leading-relaxed text-slate-500">
            <span className="font-semibold text-slate-600">Disclaimer:</span> PropChain-AI provides
            AI-assisted documentary analysis and risk indicators only. It does not establish legal
            title or replace government records and professional legal advice.
          </p>
        </div>
      </main>
    </>
  );
}
