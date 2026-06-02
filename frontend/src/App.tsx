import { useCallback, useEffect, useState } from "react";
import { api, type DayCost, type EvalRun, type EvalRunDetail, type Stats } from "./api";
import { CostChart } from "./components/CostChart";
import { RunDetail } from "./components/RunDetail";
import { RunEvalModal } from "./components/RunEvalModal";
import { RunsList } from "./components/RunsList";
import { StatsCards } from "./components/StatsCards";

type Tab = "dashboard" | "runs" | "traces";

export default function App() {
  const [tab, setTab] = useState<Tab>("dashboard");
  const [stats, setStats] = useState<Stats | null>(null);
  const [costData, setCostData] = useState<DayCost[]>([]);
  const [runs, setRuns] = useState<EvalRun[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [selectedRun, setSelectedRun] = useState<EvalRunDetail | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    try {
      const [s, c] = await Promise.all([api.stats(), api.costOverTime()]);
      setStats(s);
      setCostData(c);
    } catch {
      setError("Backend not reachable — start the API server.");
    }
  }, []);

  const loadRuns = useCallback(async () => {
    try {
      const r = await api.listRuns();
      setRuns(r);
    } catch {
      /* handled globally */
    }
  }, []);

  useEffect(() => {
    void loadDashboard();
    void loadRuns();
  }, [loadDashboard, loadRuns]);

  useEffect(() => {
    if (!selectedRunId) {
      setSelectedRun(null);
      return;
    }
    api.getRun(selectedRunId).then(setSelectedRun).catch(console.error);
  }, [selectedRunId]);

  const tabs: { id: Tab; label: string }[] = [
    { id: "dashboard", label: "Dashboard" },
    { id: "runs", label: "Runs" },
    { id: "traces", label: "Traces" },
  ];

  return (
    <div className="min-h-screen bg-zinc-950">
      {/* Header */}
      <header className="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center text-xs font-bold">
              A
            </div>
            <span className="font-semibold text-sm text-zinc-100">Agent Eval</span>
          </div>

          <nav className="flex gap-1">
            {tabs.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                  tab === t.id
                    ? "bg-zinc-800 text-zinc-100"
                    : "text-zinc-500 hover:text-zinc-300"
                }`}
              >
                {t.label}
              </button>
            ))}
          </nav>

          <button
            onClick={() => setShowModal(true)}
            className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-sm font-medium transition-colors"
          >
            + Run Eval
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        {error && (
          <div className="bg-amber-950/30 border border-amber-800/40 text-amber-400 rounded-xl px-4 py-3 text-sm">
            {error}
          </div>
        )}

        {tab === "dashboard" && (
          <>
            {stats ? (
              <StatsCards stats={stats} />
            ) : (
              <div className="grid grid-cols-5 gap-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="card h-20 animate-pulse bg-zinc-800/50" />
                ))}
              </div>
            )}
            {/* key forces remount when returning to dashboard so ResponsiveContainer re-measures */}
            <CostChart key={`cost-${costData.length}`} data={costData} />
            <div>
              <h2 className="text-sm font-semibold text-zinc-300 uppercase tracking-widest mb-3">
                Recent Runs
              </h2>
              <RunsList
                runs={runs.slice(0, 5)}
                onSelect={(id) => {
                  setSelectedRunId(id);
                  setTab("runs");
                }}
                selectedId={selectedRunId}
              />
            </div>
          </>
        )}

        {tab === "runs" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <RunsList runs={runs} onSelect={setSelectedRunId} selectedId={selectedRunId} />
            {selectedRun ? (
              <RunDetail run={selectedRun} />
            ) : (
              <div className="card text-zinc-600 text-sm text-center py-16">
                Select a run to see details
              </div>
            )}
          </div>
        )}

        {tab === "traces" && <TracesView />}
      </main>

      {showModal && (
        <RunEvalModal
          onClose={() => setShowModal(false)}
          onDone={() => {
            void loadDashboard();
            void loadRuns();
          }}
        />
      )}
    </div>
  );
}

function TracesView() {
  const [traces, setTraces] = useState<Awaited<ReturnType<typeof api.listTraces>>>([]);

  useEffect(() => {
    api.listTraces().then(setTraces).catch(console.error);
  }, []);

  if (traces.length === 0) {
    return (
      <div className="card text-zinc-600 text-sm text-center py-16">
        No traces yet — run an eval or invoke the market researcher agent.
      </div>
    );
  }

  return (
    <div className="card overflow-hidden p-0">
      <div className="px-5 py-3 border-b border-zinc-800">
        <h2 className="text-sm font-semibold text-zinc-300 uppercase tracking-widest">
          LLM Call Traces
        </h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-zinc-800 text-zinc-500">
              <th className="px-4 py-2 text-left">Time</th>
              <th className="px-4 py-2 text-left">Agent</th>
              <th className="px-4 py-2 text-left">Model</th>
              <th className="px-4 py-2 text-right">Latency</th>
              <th className="px-4 py-2 text-right">Tokens in</th>
              <th className="px-4 py-2 text-right">Tokens out</th>
              <th className="px-4 py-2 text-right">Cache hit</th>
              <th className="px-4 py-2 text-right">Cost</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/60">
            {traces.map((t) => (
              <tr key={t.id} className="hover:bg-zinc-800/30 transition-colors">
                <td className="px-4 py-2 text-zinc-500 font-mono">
                  {new Date(t.created_at).toLocaleTimeString()}
                </td>
                <td className="px-4 py-2 text-zinc-400">{t.agent_name ?? "—"}</td>
                <td className="px-4 py-2 text-zinc-400 font-mono">{t.model}</td>
                <td className="px-4 py-2 text-right text-zinc-400 font-mono">{t.latency_ms}ms</td>
                <td className="px-4 py-2 text-right text-zinc-500 font-mono">{t.input_tokens.toLocaleString()}</td>
                <td className="px-4 py-2 text-right text-zinc-500 font-mono">{t.output_tokens.toLocaleString()}</td>
                <td className="px-4 py-2 text-right font-mono">
                  {t.cache_read_tokens > 0 ? (
                    <span className="text-emerald-500">{t.cache_read_tokens.toLocaleString()}</span>
                  ) : (
                    <span className="text-zinc-700">0</span>
                  )}
                </td>
                <td className="px-4 py-2 text-right text-indigo-400 font-mono">
                  ${t.cost_usd.toFixed(5)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
