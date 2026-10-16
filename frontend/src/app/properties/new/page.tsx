"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import Navbar from "@/components/Navbar";
import { api } from "@/lib/api";

export default function NewPropertyPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [district, setDistrict] = useState("Pune");
  const [taluka, setTaluka] = useState("");
  const [village, setVillage] = useState("");
  const [surveyNumber, setSurveyNumber] = useState("");
  const [gatNumber, setGatNumber] = useState("");
  const [areaSqft, setAreaSqft] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
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
    }
  }

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-3xl px-4 py-8">
        <form onSubmit={handleSubmit} className="card space-y-4">
          <h1 className="text-2xl font-bold">Create Property Profile</h1>
          <input className="input" placeholder="Property title" value={title} onChange={(e) => setTitle(e.target.value)} required />
          <input className="input" placeholder="District" value={district} onChange={(e) => setDistrict(e.target.value)} />
          <input className="input" placeholder="Taluka" value={taluka} onChange={(e) => setTaluka(e.target.value)} />
          <input className="input" placeholder="Village" value={village} onChange={(e) => setVillage(e.target.value)} />
          <div className="grid gap-4 md:grid-cols-2">
            <input className="input" placeholder="Survey number" value={surveyNumber} onChange={(e) => setSurveyNumber(e.target.value)} />
            <input className="input" placeholder="Gat number" value={gatNumber} onChange={(e) => setGatNumber(e.target.value)} />
          </div>
          <input className="input" placeholder="Area (sqft)" value={areaSqft} onChange={(e) => setAreaSqft(e.target.value)} />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button className="btn-primary" type="submit">
            Create Property
          </button>
        </form>
      </main>
    </>
  );
}
