import type { Metadata, Viewport } from "next";
import { Bricolage_Grotesque, Figtree, Geist, Geist_Mono, Inter, Manrope } from "next/font/google";

import "./globals.css";
import "./themes/studio.css";
import "./themes/console.css";
import "./themes/enterprise.css";
import "./themes/showcase.css";

// One face per theme. Only Studio (the default) preloads; the others load when picked.
const geist = Geist({ subsets: ["latin"], variable: "--f-geist", display: "swap" });
const geistMono = Geist_Mono({ subsets: ["latin"], variable: "--f-geist-mono", display: "swap" });
const inter = Inter({ subsets: ["latin"], variable: "--f-inter", display: "swap", preload: false });
const manrope = Manrope({ subsets: ["latin"], variable: "--f-manrope", display: "swap", preload: false });
const bricolage = Bricolage_Grotesque({ subsets: ["latin"], variable: "--f-bricolage", display: "swap", preload: false });
const figtree = Figtree({ subsets: ["latin"], variable: "--f-figtree", display: "swap", preload: false });

export const metadata: Metadata = {
  title: "Talk to Omar · Hoplon & Co",
  description: "Browser demo of Omar, the AI Calling Agent. Every reply is timed and split into its parts.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const fonts = [geist, geistMono, inter, manrope, bricolage, figtree].map((f) => f.variable).join(" ");
  return (
    <html lang="en" className={fonts}>
      <body>{children}</body>
    </html>
  );
}
