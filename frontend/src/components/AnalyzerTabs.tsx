import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import {
  AlertTriangleIcon,
  BrainIcon,
  CheckCircle2Icon,
  LinkIcon,
  Loader2Icon,
  ShieldAlertIcon,
  ShieldCheckIcon,
} from "lucide-react";
import { analyzeText, AnalyzeResp } from "../lib/api";

const MIN_LEN = 3;
const MAX_LEN = 20000;

const SAMPLE = `Estimado cliente, detectamos actividad inusual en su cuenta.
Debe verificar su identidad en las próximas 24 horas o su cuenta será suspendida.
Haga clic aquí: http://secure-bank-login.top/verify`;

type Risk = "phishing" | "warning" | "safe";

const RISK_UI: Record<Risk, { label: string; ring: string; bar: string; Icon: typeof ShieldCheckIcon }> = {
  phishing: { label: "Phishing", ring: "border-red-300 bg-red-50 dark:border-red-800 dark:bg-red-950/40", bar: "bg-red-500", Icon: ShieldAlertIcon },
  warning: { label: "Sospechoso", ring: "border-amber-300 bg-amber-50 dark:border-amber-800 dark:bg-amber-950/40", bar: "bg-amber-500", Icon: AlertTriangleIcon },
  safe: { label: "Parece seguro", ring: "border-emerald-300 bg-emerald-50 dark:border-emerald-800 dark:bg-emerald-950/40", bar: "bg-emerald-500", Icon: ShieldCheckIcon },
};

/** Convierte las etiquetas de keyword (a veces patrones regex) en algo legible. */
function prettyKeyword(k: string): string {
  const known: Record<string, string> = {
    url_shortener: "acortador de URL",
    punycode_domain: "dominio punycode",
    ip_url: "URL con IP",
  };
  if (known[k]) return known[k];
  const cleaned = k
    .replace(/\\b|\(\?:|\)|\(|\)|\?|\+|\*|\[[^\]]*\]|https?:\/\//g, " ")
    .replace(/\\s|\\d\{[^}]*\}/g, " ")
    .replace(/[|]/g, " · ")
    .replace(/\s+/g, " ")
    .trim();
  return cleaned.length > 42 ? cleaned.slice(0, 42) + "…" : cleaned || k;
}

function Panel({ title, icon, children }: { title: string; icon: ReactNode; children: ReactNode }) {
  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-white p-4 dark:bg-gray-800">
      <div className="mb-2 flex items-center gap-2 text-sm font-heading font-semibold text-[var(--color-text)]">
        {icon}
        {title}
      </div>
      {children}
    </div>
  );
}

export default function Analyzer() {
  const [text, setText] = useState("");
  const [res, setRes] = useState<AnalyzeResp | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const tooShort = text.trim().length > 0 && text.trim().length < MIN_LEN;
  const canSubmit = text.trim().length >= MIN_LEN && text.length <= MAX_LEN && !loading;

  const submit = async () => {
    if (!canSubmit) return;
    setErr(null);
    setLoading(true);
    try {
      setRes(await analyzeText(text.trim(), "es"));
    } catch (e: any) {
      setErr(e?.message ?? "Error de red");
      setRes(null);
    } finally {
      setLoading(false);
    }
  };

  const risk = (res?.final?.risk as Risk) ?? null;
  const ui = risk ? RISK_UI[risk] : null;
  const score = res?.final?.score ?? 0;

  const keywords = useMemo(
    () => Array.from(new Set(res?.nb?.keywords ?? [])).slice(0, 12),
    [res],
  );

  return (
    <section id="analyzer" className="scroll-mt-20 py-12">
      <div className="mb-8 text-center">
        <h2 className="font-heading text-3xl font-bold text-[var(--color-text)]">Analiza un mensaje</h2>
        <p className="mx-auto mt-2 max-w-xl text-[var(--color-text)] opacity-70">
          Pega el contenido de un correo sospechoso. Combinamos un modelo local, reputación de URLs y una explicación con IA.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Input */}
        <div className="rounded-lg border border-[var(--color-border)] bg-white p-4 dark:bg-gray-800">
          <div className="mb-2 flex items-center justify-between text-xs text-[var(--color-text)] opacity-60">
            <button type="button" onClick={() => setText(SAMPLE)} className="hover:text-primary hover:opacity-100">
              Usar ejemplo
            </button>
            <span className={text.length > MAX_LEN ? "text-red-500" : ""}>
              {text.length.toLocaleString()} / {MAX_LEN.toLocaleString()}
            </span>
          </div>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => (e.ctrlKey || e.metaKey) && e.key === "Enter" && submit()}
            className="min-h-[220px] w-full resize-y rounded-md border border-[var(--color-border)] bg-white p-3 text-sm text-[var(--color-text)] outline-none focus:border-primary focus:ring-1 focus:ring-primary dark:bg-gray-900"
            placeholder="Asunto y cuerpo del correo…"
          />
          <div className="mt-3 flex items-center gap-3">
            <button
              onClick={submit}
              disabled={!canSubmit}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-5 py-2 font-medium text-white transition hover:shadow-md disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading && <Loader2Icon className="h-4 w-4 animate-spin" />}
              {loading ? "Analizando…" : "Analizar"}
            </button>
            <span className="text-xs text-[var(--color-text)] opacity-50">Ctrl + Enter</span>
          </div>
          {tooShort && <p className="mt-2 text-sm text-amber-600">Escribe al menos {MIN_LEN} caracteres.</p>}
          {err && <p className="mt-2 text-sm text-red-600 dark:text-red-400">{err}</p>}
        </div>

        {/* Result */}
        <div className="space-y-4">
          {!res && !loading && (
            <div className="flex h-full min-h-[260px] flex-col items-center justify-center rounded-lg border border-dashed border-[var(--color-border)] p-6 text-center text-[var(--color-text)] opacity-50">
              <ShieldCheckIcon className="mb-3 h-10 w-10" />
              El resultado aparecerá aquí.
            </div>
          )}

          {loading && (
            <div className="min-h-[260px] animate-pulse space-y-4 rounded-lg border border-[var(--color-border)] p-4">
              <div className="h-20 rounded bg-black/5 dark:bg-white/10" />
              <div className="h-24 rounded bg-black/5 dark:bg-white/10" />
            </div>
          )}

          {res && ui && (
            <>
              {/* Verdict banner */}
              <div className={`rounded-lg border p-4 ${ui.ring}`}>
                <div className="flex items-center gap-3">
                  <ui.Icon className="h-7 w-7 text-[var(--color-text)]" />
                  <div className="font-heading text-lg font-bold text-[var(--color-text)]">{ui.label}</div>
                  <div className="ml-auto text-sm font-semibold text-[var(--color-text)]">{score}/100</div>
                </div>
                <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-black/10 dark:bg-white/15">
                  <div className={`h-full rounded-full ${ui.bar}`} style={{ width: `${Math.max(3, score)}%` }} />
                </div>
                <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-[var(--color-text)] opacity-90">
                  {res.final.explanation}
                </p>
                {res.final.source && (
                  <span className="mt-2 inline-block rounded bg-black/5 px-2 py-0.5 text-[11px] text-[var(--color-text)] opacity-60 dark:bg-white/10">
                    {res.final.source}
                  </span>
                )}
              </div>

              {/* Signals */}
              <Panel title="Modelo local" icon={<BrainIcon className="h-4 w-4 text-primary" />}>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-[var(--color-text)] opacity-80">
                  <span>Veredicto: <b>{res.nb.label}</b></span>
                  <span>Probabilidad: <b>{Math.round(res.nb.phishing_score * 100)}%</b></span>
                  <span>Confianza: <b>{res.nb.confidence}</b></span>
                </div>
                {keywords.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {keywords.map((k) => (
                      <span key={k} className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary">
                        {prettyKeyword(k)}
                      </span>
                    ))}
                  </div>
                )}
              </Panel>

              <Panel title="Reputación de URLs" icon={<LinkIcon className="h-4 w-4 text-primary" />}>
                <p className="text-sm text-[var(--color-text)] opacity-80">
                  {res.safebrowsing.urls.length === 0
                    ? "No se encontraron enlaces en el mensaje."
                    : res.safebrowsing.has_threats
                    ? `${res.safebrowsing.matches.length} amenaza(s) detectada(s) por Google Safe Browsing en ${res.safebrowsing.urls.length} enlace(s).`
                    : `${res.safebrowsing.urls.length} enlace(s) analizado(s), sin amenazas conocidas.`}
                </p>
                {res.safebrowsing.urls.length > 0 && (
                  <ul className="mt-2 space-y-0.5 text-xs text-[var(--color-text)] opacity-60">
                    {res.safebrowsing.urls.slice(0, 5).map((u) => (
                      <li key={u} className="truncate">{u}</li>
                    ))}
                  </ul>
                )}
              </Panel>

              <Panel title="Explicación con IA" icon={<CheckCircle2Icon className="h-4 w-4 text-primary" />}>
                {res.llm ? (
                  <div className="text-sm text-[var(--color-text)] opacity-80">
                    <span>Veredicto: <b>{res.llm.verdict}</b></span>
                    {res.llm.advice && <p className="mt-1">{res.llm.advice}</p>}
                  </div>
                ) : (
                  <p className="text-sm text-[var(--color-text)] opacity-60">
                    {res.final.llm_error
                      ? `No disponible (${res.final.llm_error}).`
                      : "No disponible. El resultado usa solo heurísticas locales y reputación de URLs."}
                  </p>
                )}
              </Panel>
            </>
          )}
        </div>
      </div>
    </section>
  );
}
