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
      <main>
        <header className="border-b border-quiet">
          <div className="shell">
            <div className="dp-section py-10">
              <div className="dp-rail">
                <Link
                  href="/dashboard"
                  className="inline-flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.08em] text-secondary hover:text-ink"
                >
                  <ArrowLeft className="h-3.5 w-3.5" />
                  Back to portfolio
                </Link>
                <p className="eyebrow mt-6">New property file</p>
              </div>
              <div className="dp-body">
                <h1 className="font-display text-[clamp(42px,5.4cqw,72px)] font-medium leading-[0.98] tracking-[-0.035em]">
                  Create a property profile.
                </h1>
                <p className="mt-4 max-w-[38em] text-[15px] leading-[1.55] text-secondary">
                  The profile is the anchor for every cross-document check. Add the details you know
                  — anything left blank stays blank rather than being guessed.
                </p>
                <span className="mt-5 inline-flex items-center gap-2 border border-quiet px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.08em] text-secondary">
                  <Landmark className="h-3.5 w-3.5 text-ink" />
                  Maharashtra · MVP
                </span>
              </div>
            </div>
          </div>
        </header>

        <div className="shell">
          <form onSubmit={handleSubmit}>
            {error && (
              <div
                role="alert"
                className="mt-8 flex items-start gap-2.5 border border-ink px-3.5 py-3 text-[13px] leading-relaxed text-ink"
              >
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                <p>{error}</p>
              </div>
            )}

            <section className="border-b border-quiet">
              <div className="dp-section py-8">
                <div className="dp-rail">
                  <h2 className="display-subheading">Property identity</h2>
                  <p className="mt-3 max-w-[16rem] font-mono text-[10px] uppercase leading-relaxed tracking-[0.06em] text-secondary">
                    A short label you will recognise in the portfolio.
                  </p>
                </div>
                <div className="dp-body">
                  <label htmlFor="title" className="label">
                    Property title <span className="text-ink">*</span>
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
              </div>
            </section>

            <section className="border-b border-quiet">
              <div className="dp-section py-8">
                <div className="dp-rail">
                  <h2 className="flex items-center gap-2 display-subheading">
                    <MapPin className="h-4 w-4" />
                    Location
                  </h2>
                  <p className="mt-3 max-w-[16rem] font-mono text-[10px] uppercase leading-relaxed tracking-[0.06em] text-secondary">
                    District, taluka and village as written in the records.
                  </p>
                  <span className="mt-4 inline-block border border-quiet px-2 py-1 font-mono text-[9px] uppercase tracking-[0.06em] text-secondary">
                    State · Maharashtra
                  </span>
                </div>
                <div className="dp-body grid gap-5 sm:grid-cols-3">
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
              </div>
            </section>

            <section className="border-b border-quiet">
              <div className="dp-section py-8">
                <div className="dp-rail">
                  <h2 className="flex items-center gap-2 display-subheading">
                    <Hash className="h-4 w-4" />
                    Survey identifiers
                  </h2>
                  <p className="mt-3 max-w-[16rem] font-mono text-[10px] uppercase leading-relaxed tracking-[0.06em] text-secondary">
                    Used to cross-check survey, gat and CTS references across documents.
                  </p>
                </div>
                <div className="dp-body">
                  <div className="grid gap-5 sm:grid-cols-2">
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
                  <div className="mt-5 sm:max-w-xs">
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
                      <span className="pointer-events-none absolute right-3.5 top-1/2 -translate-y-1/2 font-mono text-[10px] uppercase tracking-[0.06em] text-secondary">
                        sq ft
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <section className="border-b border-quiet">
              <div className="dp-section py-8">
                <div className="dp-rail">
                  <h2 className="display-subheading">Review</h2>
                  <p className="mt-3 max-w-[16rem] font-mono text-[10px] uppercase leading-relaxed tracking-[0.06em] text-secondary">
                    Fields left blank are reported as unknown, never inferred.
                  </p>
                </div>
                <div className="dp-body flex flex-wrap items-center gap-3">
                  <button type="submit" className="btn btn-primary" disabled={loading}>
                    {loading ? <Spinner /> : null}
                    {loading ? "Creating profile…" : "Create property"}
                  </button>
                  <Link href="/dashboard" className="btn btn-ghost">
                    Cancel
                  </Link>
                </div>
              </div>
            </section>
          </form>

          <section>
            <div className="dp-section py-10">
              <div className="dp-rail">
                <p className="eyebrow">What happens next</p>
              </div>
              <div className="dp-body">
                <div className="grid gap-px bg-quiet lg:grid-cols-2">
                  <div className="bg-paper p-6">
                    <ol>
                      {STEPS.map((step, index) => (
                        <li key={step.title} className="flex gap-4 border-t border-quiet py-4 first:border-t-0 first:pt-0">
                          <span className="grid h-8 w-8 shrink-0 place-items-center border border-ink font-mono text-[10px]">
                            {index + 1}
                          </span>
                          <div>
                            <p className="font-display text-[22px] leading-none text-ink">
                              {step.title}
                            </p>
                            <p className="mt-1.5 text-[12px] leading-relaxed text-secondary">
                              {step.body}
                            </p>
                          </div>
                        </li>
                      ))}
                    </ol>
                  </div>

                  <div className="bg-paper p-6">
                    <h2 className="flex items-center gap-2 font-display text-[25px] leading-none">
                      <FileText className="h-4 w-4" />
                      Document set
                    </h2>
                    <div className="mt-4 flex flex-wrap gap-1.5">
                      {[
                        "Sale deed",
                        "7/12 extract",
                        "Property card",
                        "Encumbrance certificate",
                        "Ferfar",
                      ].map((item) => (
                        <span key={item} className="chip">
                          {item}
                        </span>
                      ))}
                    </div>
                    <div className="mt-5 flex items-start gap-2.5 border-t border-ink pt-4 text-[11px] leading-relaxed text-secondary">
                      <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-ink" />
                      <p>
                        Documents stay in the local store. Only their SHA-256 fingerprints are
                        registered on-chain.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>
      </main>
    </>
  );
}
