// In dev, use Vite proxy via /api → http://127.0.0.1:8000
// In prod, you may set VITE_API_URL to an absolute URL if needed.
const API_BASE: string = (import.meta as any).env?.DEV
  ? ""
  : (import.meta as any).env?.VITE_API_URL || "";

export type NBResult = {
  engine: string;
  label: "phishing" | "legit" | string;
  phishing_score: number;
  is_phishing: boolean;
  confidence: "low" | "medium" | "high" | string;
  keywords: string[];
};

export type LLMResult = {
  verdict: "phishing" | "safe" | "uncertain" | string;
  explanation: string;
  advice?: string;
} | null;

export type SafeBrowsing = {
  urls: string[];
  matches: any[];
  has_threats: boolean;
};

export type FinalBlock = {
  engine: string;
  score: number;
  risk: "safe" | "warning" | "phishing" | string;
  is_phishing: boolean;
  label: "phishing" | "legit" | string;
  explanation: string;
  source: string;
};

export type AnalyzeResp = {
  nb: NBResult;
  llm: LLMResult;
  safebrowsing: SafeBrowsing;
  final: FinalBlock;
};

export async function health() {
  const res = await fetch(`${API_BASE}/api/health`, { method: "GET" });
  if (!res.ok) throw new Error(`HTTP ${res.status} ${await res.text()}`);
  return res.json();
}

export async function analyze(message: string, lang: "es" | "en" = "es") {
  const res = await fetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: message.trim(), lang }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status} ${await res.text()}`);
  return (await res.json()) as AnalyzeResp;
}

// Backwards compatibility for existing code
export const analyzeText = analyze;
