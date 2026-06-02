import type { EvalRunDetail } from "../api";

interface Props {
  run: EvalRunDetail;
}

export function RunDetail({ run }: Props) {
  return (
    <div className="card space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="font-semibold text-zinc-100">{run.dataset_name}</h2>
          <div className="text-xs text-zinc-500 font-mono mt-0.5">
            {run.model} · {run.provider} · {new Date(run.created_at).toLocaleString()}
          </div>
        </div>
        <div className="text-right shrink-0">
          <div className="text-2xl font-bold text-indigo-400">
            {(run.pass_rate * 100).toFixed(1)}%
          </div>
          <div className="text-xs text-zinc-500">
            {run.passed_cases}/{run.total_cases} passed
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 text-center">
        <div className="bg-zinc-800 rounded-lg py-2 px-3">
          <div className="text-sm font-semibold text-zinc-200">${run.total_cost_usd.toFixed(5)}</div>
          <div className="text-xs text-zinc-600">total cost</div>
        </div>
        <div className="bg-zinc-800 rounded-lg py-2 px-3">
          <div className="text-sm font-semibold text-zinc-200">{run.total_latency_ms}ms</div>
          <div className="text-xs text-zinc-600">total latency</div>
        </div>
        <div className="bg-zinc-800 rounded-lg py-2 px-3">
          <div className="text-sm font-semibold text-zinc-200">{run.total_cases}</div>
          <div className="text-xs text-zinc-600">cases</div>
        </div>
      </div>

      <div className="space-y-2">
        {run.cases.map((c) => (
          <div
            key={c.case_id}
            className={`rounded-lg border p-3 ${
              c.passed
                ? "border-emerald-800/40 bg-emerald-950/20"
                : "border-red-800/40 bg-red-950/20"
            }`}
          >
            <div className="flex items-center justify-between gap-2 mb-1">
              <span className="text-xs font-mono text-zinc-300">{c.case_id}</span>
              {c.passed ? (
                <span className="badge-pass">pass</span>
              ) : (
                <span className="badge-fail">fail</span>
              )}
            </div>
            {c.output && (
              <div className="text-xs text-zinc-500 font-mono truncate mt-1 bg-zinc-900 px-2 py-1 rounded">
                {c.output.slice(0, 200)}
              </div>
            )}
            <div className="flex gap-3 mt-2 text-xs text-zinc-600">
              {c.scores?.map((s) => (
                <span key={s.scorer}>
                  {s.scorer}:{" "}
                  <span className={s.passed ? "text-emerald-500" : "text-red-500"}>
                    {s.score.toFixed(2)}
                  </span>
                </span>
              ))}
              <span>${c.cost_usd.toFixed(5)}</span>
              <span>{c.latency_ms}ms</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
