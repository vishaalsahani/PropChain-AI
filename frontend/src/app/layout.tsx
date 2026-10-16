import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PropChain-AI",
  description: "Blockchain-based AI system for property analysis",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
