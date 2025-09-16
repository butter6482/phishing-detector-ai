import { useState } from "react";
import { analyzeText, AnalyzeResp } from "../lib/api";

export default function Analyzer() {
  const [text, setText] = useState("");
  const [res, setRes] = useState<AnalyzeResp | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const submit = async () => {
    try {
      setErr(null);
      setLoading(true);
      const data = await analyzeText(text, "es");
      setRes(data);
    } catch (e: any) {
      console.error("Analyze error:", e);
      setErr(e?.message ?? "Network error");
      setRes(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid md:grid-cols-2 gap-6" id="analyzer">
      <div className="rounded-lg border p-4 bg-white dark:bg-neutral-900">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          className="w-full min-h-[180px] rounded border p-3 bg-white dark:bg-neutral-800 dark:text-white"
          placeholder="Paste the email content here..."
        />
        <button
          onClick={submit}
          disabled={loading}
          className="mt-4 inline-flex items-center px-4 py-2 rounded-lg bg-primary text-white dark:text-white hover:opacity-90"
        >
          {loading ? "Analyzing..." : "Analyze"}
        </button>
        {err && (
          <div className="mt-3 text-sm text-red-600 dark:text-red-400">{err}</div>
        )}
      </div>

      <div className="space-y-4">
        {(() => {
          const risk = res?.final?.risk;
          const colorClass =
            risk === "phishing"
              ? "border-red-400 bg-red-50 dark:bg-red-900/20"
              : risk === "warning"
              ? "border-yellow-400 bg-yellow-50 dark:bg-yellow-900/20"
              : risk === "safe"
              ? "border-green-400 bg-green-50 dark:bg-green-900/20"
              : "";
          return (
            <div className={`rounded-lg border p-4 ${colorClass}`}>
              <div className="font-semibold dark:text-white">
                {res
                  ? res.final.risk === "phishing"
                    ? "🔴 Phishing"
                    : res.final.risk === "warning"
                    ? "🟡 Warning"
                    : "🟢 Safe"
                  : "Result"}
              </div>
              <div className="mt-1 text-sm opacity-80 dark:text-neutral-300">
                Score: {res ? res.final.score : "-"} / 100
              </div>
            </div>
          );
        })()}

        <div className="rounded-lg border p-4 bg-white dark:bg-neutral-900">
          <div className="font-semibold mb-2 dark:text-white">AI Explanation</div>
          <p className="text-sm leading-6 whitespace-pre-wrap dark:text-neutral-200">
            {res?.final?.explanation ?? "-"}
          </p>
        </div>
      </div>
    </div>
  );
}
