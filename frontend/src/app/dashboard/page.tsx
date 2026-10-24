"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import Navbar from "@/components/Navbar";
import {
  Activity,
  ArrowRight,
  Flag,
  Layers,
  MapPin,
  Plus,
  Ruler,
  ShieldAlert,
  ShieldCheck,
  Spinner,
} from "@/components/icons";
import { api, Property, getToken } from "@/lib/api";
import { formatArea, formatDate, humanize, propertyStatus, riskTone } from "@/lib/presentation";

const ENGINE_LABELS: Record<string, string> = {
  api: "API",
  database: "Database",
  ocr_pipeline: "OCR",
  doc_classifier: "Classifier",
  nlp_extractor: "Extraction",
  cross_validator: "Cross-check",
  ownership_builder: "Ownership",
  rule_engine: "Rules",
  blockchain: "Blockchain",
};

const ENGINE_ORDER = [
  "ocr_pipeline",
  "doc_classifier",
  "nlp_extractor",
  "cross_validator",
  "ownership_builder",
  "rule_engine",
  "blockchain",
];

function locationOf(property: Property) {
  return [property.village, property.taluka, property.district]
    .filter((part, index, parts) => Boolean(part) && parts.indexOf(part) === index)
    .join(", ");
}

export default function DashboardPage() {
  const router = useRouter();
  const [properties, setProperties] = useState<Property[]>([]);
  const [health, setHealth] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [props, h] = await Promise.all([api.listProperties(), api.health()]);
      setProperties(props);
      setHealth(h.components);
    } catch (err) {
      const message = err instanceof Error ? err.message : "";
      if (/401|403|not authenticated|token/i.test(message)) {
        router.replace("/login");
        return;
      }
      setError("Unable to load your workspace. Check that the API is running and try again.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const stats = useMemo(() => {
    const analyzed = properties.filter((p) => p.status === "analyzed").length;
    const review = properties.filter((p) => p.status === "needs_review").length;
    const flagged = properties.filter((p) => p.status === "flagged").length;
    const scored = properties.filter((p) => p.risk_score !== null);
    const average = scored.length
      ? Math.round(scored.reduce((sum, p) => sum + (p.risk_score ?? 0), 0) / scored.length)
      : null;
    return { analyzed, review, flagged, average, scored: scored.length };
  }, [properties]);

  return (
    <>
      <Navbar />
      <main className="shell space-y-8 py-8 sm:py-10">
        <section className="animate-fade-up relative overflow-hidden rounded-3xl bg-brand-950 p-7 text-white shadow-lift sm:p-10">
          <div aria-hidden className="absolute inset-0 bg-grid-dark [background-size:32px_32px] opacity-70" />
          <div
            aria-hidden
            className="absolute -right-24 -top-32 h-80 w-80 rounded-full bg-brand-500/25 blur-3xl"
          />
          <div
            aria-hidden
            className="absolute -bottom-28 left-1/3 h-64 w-64 rounded-full bg-brass-400/10 blur-3xl"
          />
          <div className="relative flex flex-col gap-7 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="flex items-center gap-2.5 text-[11px] font-semibold uppercase tracking-[0.22em] text-brass-200/80">
                <span className="h-px w-6 bg-brass-300/50" />
                Portfolio overview
              </p>
              <h1 className="mt-4 max-w-xl font-display text-3xl font-medium leading-[1.1] text-white sm:text-[42px]">
                Your due-diligence desk.
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-relaxed text-brand-100/70">
                Upload the deed set, let the pipeline cross-check it, and read a verdict with the
                evidence behind it.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2.5">
              <Link
                href="/properties/new"
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#fffdf8] px-4 py-2.5 text-sm font-semibold text-brand-950 shadow-lg transition hover:-translate-y-px hover:bg-white"
              >
                <Plus className="h-4 w-4" />
                Add property
              </Link>
              <span className="inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/[0.06] px-3.5 py-2.5 text-xs font-medium text-brand-100/80">
                <ShieldCheck className="h-4 w-4 text-brass-200" />
                Findings, not legal conclusions
              </span>
            </div>
          </div>
        </section>

        {error && (
          <div
            role="alert"
            className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700"
          >
            <p>{error}</p>
            <button onClick={load} className="btn-secondary btn-sm border-rose-200 bg-white/70 text-rose-700">
              Retry
            </button>
          </div>
        )}

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {loading
            ? Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="card flex items-center gap-4">
                  <div className="skeleton h-11 w-11 rounded-xl" />
                  <div className="flex-1 space-y-2">
                    <div className="skeleton h-2.5 w-20" />
                    <div className="skeleton h-6 w-12" />
                  </div>
                </div>
              ))
            : [
                { label: "Properties", value: properties.length, hint: `${stats.scored} with a risk score`, icon: Layers, tone: "bg-brand-50 text-brand-700" },
                { label: "Analyzed", value: stats.analyzed, hint: "verdict recorded", icon: ShieldCheck, tone: "bg-emerald-50 text-emerald-700" },
                { label: "Needs review", value: stats.review, hint: "open items to confirm", icon: ShieldAlert, tone: "bg-amber-50 text-amber-700" },
                { label: "Flagged", value: stats.flagged, hint: stats.average === null ? "no scores yet" : `avg. risk ${stats.average}/100`, icon: Flag, tone: "bg-rose-50 text-rose-700" },
              ].map((stat, index) => (
                <div
                  key={stat.label}
                  className="card animate-fade-up flex items-center gap-4 p-5"
                  style={{ animationDelay: `${index * 60}ms` }}
                >
                  <span className={`grid h-11 w-11 shrink-0 place-items-center rounded-xl ${stat.tone}`}>
                    <stat.icon className="h-[18px] w-[18px]" />
                  </span>
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-400">
                      {stat.label}
                    </p>
                    <p className="stat-value mt-0.5 text-[28px] leading-none">{stat.value}</p>
                    <p className="mt-1 text-[11px] text-slate-400">{stat.hint}</p>
                  </div>
                </div>
              ))}
        </section>

        <div className="grid gap-6 lg:grid-cols-3">
          <section className="animate-fade-up animation-delay-100 space-y-4 lg:col-span-2">
            <div className="flex flex-wrap items-end justify-between gap-3">
              <div>
                <h2 className="text-[22px] font-medium">Your properties</h2>
                <p className="mt-0.5 text-sm text-slate-500">
                  Every uploaded file belongs to one property profile.
                </p>
              </div>
              <span className="chip">
                {properties.length} {properties.length === 1 ? "property" : "properties"}
              </span>
            </div>

            {loading ? (
              <div className="grid gap-4 sm:grid-cols-2">
                {Array.from({ length: 4 }).map((_, index) => (
                  <div key={index} className="card space-y-4">
                    <div className="skeleton h-5 w-3/4" />
                    <div className="skeleton h-3 w-1/2" />
                    <div className="flex gap-2">
                      <div className="skeleton h-6 w-20" />
                      <div className="skeleton h-6 w-16" />
                    </div>
                    <div className="skeleton h-1.5 w-full" />
                  </div>
                ))}
              </div>
            ) : properties.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-ink/15 bg-white/50 px-6 py-14 text-center">
                <span className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-brand-50 text-brand-700 ring-1 ring-inset ring-brand-600/10">
                  <Layers className="h-6 w-6" />
                </span>
                <h3 className="mt-5 text-xl font-medium">Start with a property file</h3>
                <p className="mx-auto mt-2 max-w-sm text-sm leading-relaxed text-slate-500">
                  Create a profile with the village, survey number and area, then upload the deed set
                  to run the first analysis.
                </p>
                <Link href="/properties/new" className="btn-primary mt-6">
                  <Plus className="h-4 w-4" />
                  Add a property
                </Link>
              </div>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2">
                {properties.map((property, index) => {
                  const status = propertyStatus(property.status);
                  const risk = riskTone(property.risk_score);
                  const location = locationOf(property);
                  return (
                    <Link
                      key={property.id}
                      href={`/properties/${property.id}`}
                      className="group animate-fade-up relative flex flex-col overflow-hidden rounded-2xl border border-ink/[0.06] bg-white/80 shadow-soft backdrop-blur-sm transition duration-300 hover:-translate-y-0.5 hover:border-brand-200 hover:shadow-lift"
                      style={{ animationDelay: `${80 + index * 50}ms` }}
                    >
                      <span className={`h-1 w-full ${status.accent}`} />
                      <div className="flex flex-1 flex-col p-5">
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <h3 className="line-clamp-2 text-[17px] font-medium leading-snug transition group-hover:text-brand-800">
                              {property.title}
                            </h3>
                            <p className="mt-1.5 flex items-center gap-1.5 text-xs text-slate-500">
                              <MapPin className="h-3.5 w-3.5 shrink-0 text-slate-400" />
                              {location || "Location not set"}
                            </p>
                          </div>
                          <span className={`${status.badge} shrink-0`}>
                            <span className={`h-1.5 w-1.5 rounded-full ${status.dot}`} />
                            {status.label}
                          </span>
                        </div>

                        <div className="mt-4 flex flex-wrap gap-1.5">
                          {property.survey_number && (
                            <span className="chip">Survey {property.survey_number}</span>
                          )}
                          {property.gat_number && <span className="chip">Gat {property.gat_number}</span>}
                          {property.area_sqft !== null && property.area_sqft !== undefined && (
                            <span className="chip">
                              <Ruler className="h-3 w-3 text-slate-400" />
                              {formatArea(property.area_sqft)}
                            </span>
                          )}
                        </div>

                        <div className="mt-auto pt-6">
                          <div className="flex items-center justify-between text-[11px]">
                            <span className="text-slate-400">Risk indicator</span>
                            <span className={`font-semibold ${risk.text}`}>
                              {property.risk_score === null ? "Not scored" : `${Math.round(property.risk_score)}/100`}
                            </span>
                          </div>
                          <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-ink/[0.06]">
                            <div
                              className={`h-full rounded-full ${risk.bar} transition-all duration-500`}
                              style={{ width: `${Math.min(Math.max(property.risk_score ?? 0, 0), 100)}%` }}
                            />
                          </div>
                          <div className="mt-3 flex items-center justify-between border-t border-ink/[0.06] pt-3 text-[11px] text-slate-400">
                            <span>Created {formatDate(property.created_at)}</span>
                            <span className="inline-flex items-center gap-1 font-semibold text-brand-700">
                              Open file
                              <ArrowRight className="h-3.5 w-3.5 transition group-hover:translate-x-0.5" />
                            </span>
                          </div>
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </section>

          <aside className="animate-fade-up animation-delay-200 space-y-6">
            <div className="card">
              <div className="flex items-center justify-between">
                <h2 className="flex items-center gap-2 text-base font-semibold">
                  <Activity className="h-4 w-4 text-brand-700" />
                  Analysis pipeline
                </h2>
                <span className="inline-flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-emerald-700">
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
                  Live
                </span>
              </div>
              <p className="mt-1 text-xs text-slate-400">Engines selected for this deployment.</p>

              <div className="mt-4 grid grid-cols-2 gap-2">
                {(loading ? ENGINE_ORDER : ENGINE_ORDER.filter((key) => health[key])).map((key) => {
                  const value = health[key];
                  const isMock = value === "mock";
                  return (
                    <div
                      key={key}
                      className="rounded-xl border border-ink/[0.06] bg-white/60 px-3 py-2.5"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-400">
                          {ENGINE_LABELS[key] ?? humanize(key)}
                        </p>
                        <span
                          className={`h-1.5 w-1.5 shrink-0 rounded-full ${
                            loading ? "bg-slate-300" : isMock ? "bg-amber-400" : "bg-emerald-500"
                          }`}
                        />
                      </div>
                      {loading ? (
                        <div className="skeleton mt-1.5 h-3 w-16" />
                      ) : (
                        <p className="mt-0.5 truncate text-xs font-semibold text-ink">{humanize(value ?? "—")}</p>
                      )}
                    </div>
                  );
                })}
              </div>

              <div className="mt-4 flex items-center justify-between rounded-xl bg-brand-50/70 px-3 py-2.5 text-[11px] text-brand-800">
                <span className="inline-flex items-center gap-1.5">
                  <ShieldCheck className="h-3.5 w-3.5" />
                  Documents stay off-chain
                </span>
                <span className="font-mono text-[10px] text-brand-600">SHA-256</span>
              </div>
            </div>

            <div className="card">
              <h2 className="text-base font-semibold">How verdicts are read</h2>
              <p className="mt-1 text-xs text-slate-400">
                Project policy — findings are screening indicators.
              </p>
              <ul className="mt-4 space-y-3.5">
                {[
                  {
                    icon: ShieldCheck,
                    tone: "bg-emerald-50 text-emerald-700",
                    title: "Verified",
                    body: "No medium-or-higher findings and no ownership gaps.",
                  },
                  {
                    icon: ShieldAlert,
                    tone: "bg-amber-50 text-amber-700",
                    title: "Needs review",
                    body: "Only low/medium items, or no completed documents yet.",
                  },
                  {
                    icon: Flag,
                    tone: "bg-rose-50 text-rose-700",
                    title: "Flagged",
                    body: "A high/critical finding or any gap in the ownership chain.",
                  },
                ].map((item) => (
                  <li key={item.title} className="flex gap-3">
                    <span className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg ${item.tone}`}>
                      <item.icon className="h-4 w-4" />
                    </span>
                    <div>
                      <p className="text-[13px] font-semibold text-ink">{item.title}</p>
                      <p className="mt-0.5 text-[11px] leading-relaxed text-slate-500">{item.body}</p>
                    </div>
                  </li>
                ))}
              </ul>
              <p className="mt-4 border-t border-ink/[0.06] pt-3 text-[11px] leading-relaxed text-slate-400">
                Items that could not be checked (RERA, litigation history, encumbrance) are always
                listed alongside the verdict.
              </p>
            </div>
          </aside>
        </div>

        {loading && (
          <div className="flex items-center justify-center gap-2 py-2 text-xs text-slate-400">
            <Spinner className="h-3.5 w-3.5" />
            Loading your workspace…
          </div>
        )}
      </main>
    </>
  );
}
