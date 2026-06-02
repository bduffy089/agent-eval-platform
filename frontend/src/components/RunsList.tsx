import type { EvalRun } from "../api";

interface Props {
  runs: EvalRun[];
  onSelect: (id: string) => void;
  selectedId: string | null;
}

function passRateBadge(rate: number) {
  const pct = (rate * 100).toFixed(1);
  return rate >= 0.8 ? (
    <span className="badge-pass">✓ {pct}%</span>
  ) : (
    <span className="badge-fail">✗ {pct}%</span>
  );
}

export function RunsList({ runs, onSelect, selectedId }: Props) {
  if (runs.length === 0) {
    return (
      <div className="card text-zinc-600 text-sm text-center py-10">
        No eval runs yet. Use the "Run Eval" button to get started.
      </div>
    );
  }

  return (
    <div className="card overflow-hidden p-0">
      <div className="px-5 py-3 border-b border-zinc-800">
        <h2 className="text-sm font-semibold text-zinc-300 uppercase tracking-widest">
          Recent Runs
        </h2>
      </div>
      <div className="divide-y divide-zinc-800">
        {runs.map((r) => (
          <button
            key={r.id}
            onClick={() => onSelect(r.id)}
            className={`w-full text-left px-5 py-3.5 hover:bg-zinc-800/50 transition-colors ${
              selectedId === r.id ? "bg-zinc-800" : ""
            }`}
          >
            <div className="flex items-center justify-between gap-4">
              <div className="min-w-0">
                <div className="font-medium text-sm text-zinc-200 truncate">
                  {r.dataset_name}
                </div>
                <div className="text-xs text-zinc-500 mt-0.5 font-mono">
                  {r.model} · {r.total_cases} cases
                </div>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                {passRateBadge(r.pass_rate)}
                <span className="text-xs text-zinc-500 font-mono">
                  ${r.total_cost_usd.toFixed(4)}
                </span>
                <span className="text-xs text-zinc-600">
                  {new Date(r.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
