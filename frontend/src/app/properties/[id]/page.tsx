"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import DocumentUploader, { DocumentList } from "@/components/DocumentUploader";
import FindingsList from "@/components/FindingsList";
import OwnershipTimeline from "@/components/OwnershipTimeline";
import ReviewPanel from "@/components/ReviewPanel";
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
  AnalysisRunSummary,
  DocumentItem,
  Finding,
  FindingReviewStatus,
  OwnershipNode,
  Property,
  UserOut,
  VerdictOut,
  getToken,
} from "@/lib/api";
import { formatArea, formatDate, propertyStatus } from "@/lib/presentation";

type Notice = { text: string; tone: "success" | "warning" | "danger" | "info" };

const NOTICE_STYLES: Record<Notice["tone"], string> = {
  success: "border-ink",
  warning: "border-ink",
  danger: "border-ink",
  info: "border-ink",
};

export default function PropertyDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const propertyId = Number(id);
  const [property, setProperty] = useState<Property | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [ownership, setOwnership] = useState<OwnershipNode[]>([]);
  const [verdict, setVerdict] = useState<VerdictOut | null>(null);
  const [runs, setRuns] = useState<AnalysisRunSummary[]>([]);
  const [me, setMe] = useState<UserOut | null>(null);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    const [prop, docs, findingList, chain, runList, currentUser] = await Promise.all([
      api.getProperty(propertyId),
      api.listDocuments(propertyId),
      api.getFindings(propertyId),
      api.getOwnership(propertyId),
      api.listRuns(propertyId).catch(() => []),
      api.me().catch(() => null),
    ]);
    setProperty(prop);
    setDocuments(docs);
    setFindings(findingList);
    setOwnership(chain);
    setRuns(runList);
    setMe(currentUser);
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

  async function reviewFinding(
    findingId: number,
    status: FindingReviewStatus,
    note: string,
    expectedStatus: FindingReviewStatus
  ) {
    const updated = await api.reviewFinding(findingId, {
      status,
      note: note || null,
      expected_status: expectedStatus,
    });
    setFindings((current) =>
      current.map((finding) => (finding.id === findingId ? updated : finding))
    );
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
        <main className="shell py-10">
          <div className="skeleton h-3 w-40" />
          <div className="skeleton mt-6 h-12 w-2/3 max-w-xl" />
          <div className="skeleton mt-4 h-3 w-1/3" />
          <div className="mt-12 grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">
            <div className="skeleton h-72 w-full" />
            <div className="skeleton h-72 w-full" />
          </div>
          <div className="mt-6 skeleton h-56 w-full" />
        </main>
      </>
    );
  }

  if (!property) {
    return (
      <>
        <Navbar />
        <main className="shell py-16">
          <div className="mx-auto max-w-xl border border-ink p-8 text-center">
            <AlertTriangle className="mx-auto h-8 w-8 text-ink" />
            <h1 className="mt-4 font-display text-[32px] leading-none">This file could not be opened</h1>
            <p className="mt-3 text-[13px] leading-relaxed text-secondary">
              {error || "The property was not found."}
            </p>
            <Link href="/dashboard" className="btn btn-secondary mt-6">
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
  const canReview = me?.role === "reviewer" || me?.role === "admin";
  const canEdit = me?.role === "buyer" || me?.role === "owner";
  const latestRun = runs[0] ?? null;

  return (
    <>
      <Navbar />
      <main>
        <header className="border-b border-quiet">
          <div className="shell py-10">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.08em] text-secondary hover:text-ink"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Portfolio
            </Link>

            <div className="mt-6 flex flex-wrap items-end justify-between gap-8">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-3">
                  <span className={status.badge}>
                    <span className={`h-1.5 w-1.5 ${status.dot}`} />
                    {status.label}
                  </span>
                  <span className="inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.07em] text-secondary">
                    <Calendar className="h-3.5 w-3.5" />
                    Created {formatDate(property.created_at)}
                  </span>
                  {canReview && (
                    <span className="border border-ink px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.08em]">
                      Reviewer view
                    </span>
                  )}
                </div>
                <h1 className="mt-4 max-w-[15em] font-display text-[clamp(40px,5.8cqw,78px)] font-medium leading-[0.98] tracking-[-0.035em]">
                  {property.title}
                </h1>
                <p className="mt-3 flex items-center gap-2 text-[14px] text-secondary">
                  <MapPin className="h-4 w-4 shrink-0" />
                  {location || "Location not set"}
                </p>
                <div className="mt-5 flex flex-wrap gap-1.5">
                  <span className="chip">
                    <Hash className="h-3.5 w-3.5" />
                    Survey {property.survey_number || "—"}
                  </span>
                  <span className="chip">
                    <Hash className="h-3.5 w-3.5" />
                    Gat {property.gat_number || "—"}
                  </span>
                  <span className="chip">
                    <Ruler className="h-3.5 w-3.5" />
                    {formatArea(property.area_sqft)}
                  </span>
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                {canEdit && (
                  <button
                    className="btn btn-primary"
                    onClick={runAnalysis}
                    disabled={running}
                    aria-busy={running}
                  >
                    {running ? <Spinner /> : <Sparkles className="h-4 w-4" />}
                    {running ? "Running analysis…" : "Run analysis"}
                  </button>
                )}
                <button
                  className="btn btn-secondary"
                  onClick={downloadReport}
                  disabled={downloading}
                >
                  {downloading ? <Spinner /> : <Download className="h-4 w-4" />}
                  {downloading ? "Preparing…" : "Report"}
                </button>
              </div>
            </div>
          </div>
        </header>

        <div className="shell">
          {notice && (
            <div
              role="status"
              className={`mt-6 flex items-start gap-3 border px-4 py-3.5 text-[13px] leading-relaxed text-ink ${NOTICE_STYLES[notice.tone]}`}
            >
              {notice.tone === "success" ? (
                <Sparkles className="mt-0.5 h-4 w-4 shrink-0" />
              ) : (
                <Info className="mt-0.5 h-4 w-4 shrink-0" />
              )}
              <p className="flex-1">{notice.text}</p>
              <button
                onClick={() => setNotice(null)}
                className="p-1 hover:text-secondary"
                aria-label="Dismiss message"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )}

          {error && (
            <div
              role="alert"
              className="mt-6 flex items-start gap-3 border border-ink px-4 py-3.5 text-[13px] leading-relaxed text-ink"
            >
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <p className="flex-1">{error}</p>
              <button
                onClick={() => setError("")}
                className="p-1 hover:text-secondary"
                aria-label="Dismiss error"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )}

          <section className="border-b border-quiet">
            <div className="dp-section py-10">
              <div className="dp-rail">
                <h2 className="display-heading">Screening summary</h2>
                <p className="mt-4 max-w-[18rem] text-[13px] leading-relaxed text-secondary">
                  The verdict is a screening output under the selected rule pack. Unknowns stay
                  visible.
                </p>
              </div>
              <div className="dp-body">
                <div className="grid items-start gap-5 lg:grid-cols-[1.25fr_0.75fr]">
                  <VerdictBadge verdict={verdict} />
                  <RiskIndicator score={property.risk_score} />
                </div>
              </div>
            </div>
          </section>

          {(canReview || runs.length > 0) && (
            <section className="border-b border-quiet">
              <div className="dp-section py-10">
                <div className="dp-rail">
                  <h2 className="display-heading">Human review</h2>
                  <p className="mt-4 max-w-[18rem] text-[13px] leading-relaxed text-secondary">
                    A reviewer can confirm the system result or record an override. The original run
                    stays intact.
                  </p>
                  {latestRun && (
                    <span className="mt-5 inline-block border border-quiet px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.08em] text-secondary">
                      {latestRun.review_status === "pending"
                        ? "Awaiting reviewer"
                        : `Reviewed · ${latestRun.review_status}`}
                    </span>
                  )}
                </div>
                <div className="dp-body">
                  <ReviewPanel
                    latestRun={latestRun}
                    runs={runs}
                    canReview={canReview}
                    onUpdated={refresh}
                  />
                </div>
              </div>
            </section>
          )}

          <section className="border-b border-quiet">
            <div className="dp-section py-10">
              <div className="dp-rail">
                <h2 className="display-heading">Documents</h2>
                <p className="mt-4 max-w-[18rem] text-[13px] leading-relaxed text-secondary">
                  Every file stays in the off-chain store. Only its SHA-256 fingerprint is
                  registered.
                </p>
                <span className="mt-5 inline-block border border-quiet px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.08em] text-secondary">
                  {documents.length} {documents.length === 1 ? "file" : "files"} ·{" "}
                  {documents.filter((doc) => doc.status === "completed").length} processed
                </span>
              </div>
              <div className="dp-body">
                {canEdit && <DocumentUploader propertyId={propertyId} onUploaded={refresh} />}
                <div className={canEdit ? "mt-8" : ""}>
                  <div className="flex flex-wrap items-end justify-between gap-3 border-b border-ink pb-3">
                    <h3 className="font-display text-[26px] leading-none">Files</h3>
                    <span className="font-mono text-[10px] uppercase tracking-[0.06em] text-secondary">
                      Hash-anchored records
                    </span>
                  </div>
                  <DocumentList
                    documents={documents}
                    onAction={refresh}
                    canManage={canEdit}
                  />
                </div>
              </div>
            </div>
          </section>

          <section className="border-b border-quiet">
            <div className="dp-section py-10">
              <div className="dp-rail">
                <h2 className="display-heading">Findings</h2>
                <p className="mt-4 max-w-[18rem] text-[13px] leading-relaxed text-secondary">
                  Inconsistencies raised by the matrix and the Maharashtra rule pack.
                </p>
                {findings.length > 0 && (
                  <span className="mt-5 inline-block border border-ink bg-ink px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.08em] text-paper">
                    {findings.length} {findings.length === 1 ? "finding" : "findings"}
                  </span>
                )}
              </div>
              <div className="dp-body">
                <FindingsList
                  findings={findings}
                  hasRun={Boolean(verdict)}
                  canReview={canReview}
                  onReview={reviewFinding}
                />
              </div>
            </div>
          </section>

          <section className="border-b border-quiet">
            <div className="dp-section py-10">
              <div className="dp-rail">
                <h2 className="display-heading">Ownership chain</h2>
                <p className="mt-4 max-w-[18rem] text-[13px] leading-relaxed text-secondary">
                  The sequence of transfers, traced from the root record.
                </p>
                {ownership.length > 0 && (
                  <span className="mt-5 inline-block border border-quiet px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.08em] text-secondary">
                    {ownership.length} {ownership.length === 1 ? "step" : "steps"}
                  </span>
                )}
              </div>
              <div className="dp-body">
                <OwnershipTimeline nodes={ownership} />
              </div>
            </div>
          </section>
        </div>

        <footer className="border-t-[3px] border-ink">
          <div className="shell flex items-start gap-3 py-6">
            <span className="grid h-8 w-8 shrink-0 place-items-center border border-ink text-ink">
              <Info className="h-4 w-4" />
            </span>
            <p className="text-[11px] leading-relaxed text-secondary">
              <span className="font-medium text-ink">Disclaimer:</span> PropChain-AI provides
              AI-assisted documentary analysis and risk indicators only. It does not establish legal
              title or replace government records and professional legal advice.
            </p>
          </div>
        </footer>
      </main>
    </>
  );
}
