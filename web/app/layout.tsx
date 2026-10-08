import type { Metadata, Viewport } from "next";
import { Bricolage_Grotesque, Epilogue, Figtree, Geist, Geist_Mono, Manrope } from "next/font/google";

import "./globals.css";
import "./themes/studio.css";
import "./themes/console.css";
import "./themes/enterprise.css";
import "./themes/showcase.css";

// One face per theme. Only Console (the default) preloads; the others load when picked.
const geist = Geist({ subsets: ["latin"], variable: "--f-geist", display: "swap", preload: false });
const geistMono = Geist_Mono({ subsets: ["latin"], variable: "--f-geist-mono", display: "swap", preload: false });
const epilogue = Epilogue({ subsets: ["latin"], variable: "--f-epilogue", display: "swap" });
const manrope = Manrope({ subsets: ["latin"], variable: "--f-manrope", display: "swap", preload: false });
const bricolage = Bricolage_Grotesque({ subsets: ["latin"], variable: "--f-bricolage", display: "swap", preload: false });
const figtree = Figtree({ subsets: ["latin"], variable: "--f-figtree", display: "swap", preload: false });

export const metadata: Metadata = {
  title: "Talk to Nimra · Hoplon & Co",
  description: "Browser demo of Nimra, the AI Calling Agent. Every reply is timed and split into its parts.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const fonts = [geist, geistMono, epilogue, manrope, bricolage, figtree].map((f) => f.variable).join(" ");
  return (
    <html lang="en" className={fonts}>
      <body>{children}</body>
    </html>
  );
}
