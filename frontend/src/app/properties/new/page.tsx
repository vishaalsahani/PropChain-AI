"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import Navbar from "@/components/Navbar";
import {
  AlertTriangle,
  ArrowLeft,
  FileText,
  Hash,
  Landmark,
  MapPin,
  Ruler,
  ShieldCheck,
  Spinner,
} from "@/components/icons";
import { api } from "@/lib/api";

const STEPS = [
  {
    title: "Upload the document set",
    body: "Sale deed, 7/12 extract, property card, encumbrance certificate or ferfar.",
  },
  {
    title: "Run the analysis",
    body: "OCR and field extraction in English and Marathi, then cross-document checks.",
  },
  {
    title: "Read the verdict",
    body: "Reasons, the ownership chain and the items that could not be checked.",
  },
];

export default function NewPropertyPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [district, setDistrict] = useState("Pune");
  const [taluka, setTaluka] = useState("");
  const [village, setVillage] = useState("");
  const [surveyNumber, setSurveyNumber] = useState("");
  const [gatNumber, setGatNumber] = useState("");
  const [areaSqft, setAreaSqft] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const prop = await api.createProperty({
        title,
        state: "Maharashtra",
        district,
        taluka,
        village,
        survey_number: surveyNumber,
        gat_number: gatNumber,
        area_sqft: areaSqft ? Number(areaSqft) : undefined,
      });
      router.push(`/properties/${prop.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create property");
      setLoading(false);
    }
  }

  return (
    <>
      <Navbar />
      <main className="shell space-y-8 py-8 sm:py-10">
        <div className="animate-fade-up">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 transition hover:text-brand-700"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to portfolio
          </Link>
          <div className="mt-5 flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="eyebrow">New property file</p>
              <h1 className="mt-2 text-[32px] font-medium leading-tight">Create a property profile.</h1>
              <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-500">
                The profile is the anchor for every cross-document check. Add the details you know —
                anything left blank stays blank rather than being guessed.
              </p>
            </div>
            <span className="chip">
              <Landmark className="h-3.5 w-3.5 text-brand-700" />
              Maharashtra · MVP
            </span>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <form
            onSubmit={handleSubmit}
            className="card animate-fade-up animation-delay-100 space-y-7 lg:col-span-2"
          >
            {error && (
              <div
                role="alert"
                className="flex items-start gap-2.5 rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-3 text-sm text-rose-700"
              >
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                <p>{error}</p>
              </div>
            )}

            <section className="space-y-4">
              <div>
                <h2 className="text-base font-semibold">Property identity</h2>
                <p className="mt-0.5 text-xs text-slate-400">
                  A short label you will recognise in the portfolio.
                </p>
              </div>
              <div>
                <label htmlFor="title" className="label">
                  Property title <span className="text-rose-500">*</span>
                </label>
                <input
                  id="title"
                  className="input"
                  placeholder="e.g. Wagholi plot — survey 42/2"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                />
              </div>
            </section>

            <div className="divider" />

            <section className="space-y-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="flex items-center gap-2 text-base font-semibold">
                    <MapPin className="h-4 w-4 text-brand-700" />
                    Location
                  </h2>
                  <p className="mt-0.5 text-xs text-slate-400">District, taluka and village as written in the records.</p>
                </div>
                <span className="chip text-[10px] uppercase tracking-wide">State · Maharashtra</span>
              </div>
              <div className="grid gap-4 sm:grid-cols-3">
                <div>
                  <label htmlFor="district" className="label">
                    District
                  </label>
                  <input
                    id="district"
                    className="input"
                    placeholder="Pune"
                    value={district}
                    onChange={(e) => setDistrict(e.target.value)}
                  />
                </div>
                <div>
                  <label htmlFor="taluka" className="label">
                    Taluka
                  </label>
                  <input
                    id="taluka"
                    className="input"
                    placeholder="Haveli"
                    value={taluka}
                    onChange={(e) => setTaluka(e.target.value)}
                  />
                </div>
                <div>
                  <label htmlFor="village" className="label">
                    Village
                  </label>
                  <input
                    id="village"
                    className="input"
                    placeholder="Wagholi"
                    value={village}
                    onChange={(e) => setVillage(e.target.value)}
                  />
                </div>
              </div>
            </section>

            <div className="divider" />

            <section className="space-y-4">
              <div>
                <h2 className="flex items-center gap-2 text-base font-semibold">
                  <Hash className="h-4 w-4 text-brand-700" />
                  Survey identifiers
                </h2>
                <p className="mt-0.5 text-xs text-slate-400">
                  Used to cross-check survey, gat and CTS references across documents.
                </p>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label htmlFor="survey-number" className="label">
                    Survey number
                  </label>
                  <input
                    id="survey-number"
                    className="input"
                    placeholder="42/2"
                    value={surveyNumber}
                    onChange={(e) => setSurveyNumber(e.target.value)}
                  />
                </div>
                <div>
                  <label htmlFor="gat-number" className="label">
                    Gat number
                  </label>
                  <input
                    id="gat-number"
                    className="input"
                    placeholder="Optional"
                    value={gatNumber}
                    onChange={(e) => setGatNumber(e.target.value)}
                  />
                </div>
              </div>
              <div className="sm:max-w-xs">
                <label htmlFor="area" className="label">
                  <span className="inline-flex items-center gap-1.5">
                    <Ruler className="h-3.5 w-3.5" />
                    Area
                  </span>
                </label>
                <div className="relative">
                  <input
                    id="area"
                    className="input pr-16"
                    type="number"
                    min="0"
                    step="any"
                    inputMode="decimal"
                    placeholder="0"
                    value={areaSqft}
                    onChange={(e) => setAreaSqft(e.target.value)}
                  />
                  <span className="pointer-events-none absolute right-3.5 top-1/2 -translate-y-1/2 text-xs font-medium text-slate-400">
                    sq ft
                  </span>
                </div>
              </div>
            </section>

            <div className="flex flex-wrap items-center gap-3 border-t border-ink/[0.06] pt-5">
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? <Spinner /> : null}
                {loading ? "Creating profile…" : "Create property"}
              </button>
              <Link href="/dashboard" className="btn-ghost">
                Cancel
              </Link>
              <p className="ml-auto text-[11px] text-slate-400">
                Fields left blank are reported as unknown, never inferred.
              </p>
            </div>
          </form>

          <aside className="animate-fade-up animation-delay-200 space-y-6">
            <div className="card">
              <p className="eyebrow">What happens next</p>
              <ol className="mt-4 space-y-4">
                {STEPS.map((step, index) => (
                  <li key={step.title} className="flex gap-3">
                    <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-brand-900 text-[11px] font-bold text-white">
                      {index + 1}
                    </span>
                    <div>
                      <p className="text-[13px] font-semibold text-ink">{step.title}</p>
                      <p className="mt-0.5 text-[11px] leading-relaxed text-slate-500">{step.body}</p>
                    </div>
                  </li>
                ))}
              </ol>
            </div>

            <div className="card">
              <h2 className="flex items-center gap-2 text-base font-semibold">
                <FileText className="h-4 w-4 text-brand-700" />
                Document set
              </h2>
              <div className="mt-3 flex flex-wrap gap-1.5">
                {["Sale deed", "7/12 extract", "Property card", "Encumbrance certificate", "Ferfar"].map(
                  (item) => (
                    <span key={item} className="chip">
                      {item}
                    </span>
                  ),
                )}
              </div>
              <div className="mt-4 flex items-start gap-2.5 rounded-xl bg-brand-50/70 p-3 text-[11px] leading-relaxed text-brand-800">
                <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" />
                <p>
                  Documents stay in the local store. Only their SHA-256 fingerprints are registered
                  on-chain.
                </p>
              </div>
            </div>
          </aside>
        </div>
      </main>
    </>
  );
}
