import fs from "node:fs";
import path from "node:path";
import type { NextConfig } from "next";

// One .env for the whole repo: load ../.env for keys that are not set yet.
const rootEnv = path.resolve(process.cwd(), "..", ".env");
if (fs.existsSync(rootEnv)) {
  for (const line of fs.readFileSync(rootEnv, "utf8").split("\n")) {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*(#.*)?$/);
    if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^["']|["']$/g, "");
  }
}

const config: NextConfig = {
  reactStrictMode: true,
};

export default config;
