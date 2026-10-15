import type { Metadata, Viewport } from "next";
import { Bricolage_Grotesque, Epilogue, Figtree, Geist, Geist_Mono, Manrope, Space_Grotesk } from "next/font/google";

import "./globals.css";
import "./themes/studio.css";
import "./themes/console.css";
import "./themes/enterprise.css";
import "./themes/showcase.css";
import "./themes/horizon.css";

// One face per theme. Horizon (the default) preloads Epilogue and Space Grotesk; the others load when picked.
const geist = Geist({ subsets: ["latin"], variable: "--f-geist", display: "swap", preload: false });
const geistMono = Geist_Mono({ subsets: ["latin"], variable: "--f-geist-mono", display: "swap", preload: false });
const epilogue = Epilogue({ subsets: ["latin"], variable: "--f-epilogue", display: "swap" });
const manrope = Manrope({ subsets: ["latin"], variable: "--f-manrope", display: "swap", preload: false });
const bricolage = Bricolage_Grotesque({ subsets: ["latin"], variable: "--f-bricolage", display: "swap", preload: false });
const space = Space_Grotesk({ subsets: ["latin"], weight: ["400", "500"], variable: "--f-space", display: "swap" });
const figtree = Figtree({ subsets: ["latin"], variable: "--f-figtree", display: "swap", preload: false });

export const metadata: Metadata = {
  title: "Talk to Uzair · Hoplon & Co",
  description: "Uzair, Hoplon & Co's AI calling agent, calls you in the browser. Type your name, pick who you are, and talk.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#0a0a0a",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const fonts = [geist, geistMono, epilogue, manrope, bricolage, figtree, space].map((f) => f.variable).join(" ");
  return (
    <html lang="en" className={fonts}>
      <body>{children}</body>
    </html>
  );
}
