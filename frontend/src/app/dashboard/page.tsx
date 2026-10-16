"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import { api, Property } from "@/lib/api";

export default function DashboardPage() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [health, setHealth] = useState<Record<string, string>>({});
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.listProperties(), api.health()])
      .then(([props, h]) => {
        setProperties(props);
        setHealth(h.components);
      })
      .catch(() => setError("Please login to continue"));
  }, []);

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 py-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Dashboard</h1>
            <p className="text-sm text-slate-500">Property due diligence overview</p>
          </div>
          <Link href="/properties/new" className="btn-primary">
            Add Property
          </Link>
        </div>

        {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

        <div className="mb-8 grid gap-4 md:grid-cols-4">
          {Object.entries(health).map(([key, value]) => (
            <div key={key} className="card">
              <p className="text-xs uppercase text-slate-500">{key}</p>
              <p className="mt-1 font-medium capitalize">{value}</p>
            </div>
          ))}
        </div>

        <div className="card">
          <h2 className="mb-4 text-lg font-semibold">Your Properties</h2>
          {!properties.length ? (
            <p className="text-sm text-slate-500">No properties yet. Create one to begin.</p>
          ) : (
            <div className="space-y-3">
              {properties.map((prop) => (
                <Link
                  key={prop.id}
                  href={`/properties/${prop.id}`}
                  className="block rounded-lg border border-slate-200 p-4 hover:border-brand-500"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">{prop.title}</p>
                      <p className="text-sm text-slate-500">
                        {prop.village}, {prop.district}, {prop.state}
                      </p>
                    </div>
                    <div className="text-right text-sm">
                      <p className="capitalize">{prop.status}</p>
                      <p className="text-slate-500">Risk: {prop.risk_score ?? "N/A"}</p>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
    </>
  );
}
