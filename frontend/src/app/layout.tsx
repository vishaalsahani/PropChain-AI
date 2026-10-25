import type { Metadata } from "next";
import { EB_Garamond, IBM_Plex_Mono, Source_Serif_4 } from "next/font/google";
import "./globals.css";

const display = EB_Garamond({
  subsets: ["latin"],
  variable: "--font-eb-garamond",
  display: "swap",
});

const text = Source_Serif_4({
  subsets: ["latin"],
  variable: "--font-source-serif",
  display: "swap",
});

const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-ibm-plex-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "PropChain-AI",
    template: "%s · PropChain-AI",
  },
  description:
    "AI-assisted property due diligence for Maharashtra: document extraction, cross-verification and evidence-based ownership chains.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${display.variable} ${text.variable} ${mono.variable}`}
    >
      <body className="min-h-screen">
        {/* The explicit wrapper keeps the text face in charge even when a
            browser extension injects a body-level font override. */}
        <div className="font-text" style={{ fontFamily: "var(--dp-typography-text)" }}>
          {children}
        </div>
      </body>
    </html>
  );
}
