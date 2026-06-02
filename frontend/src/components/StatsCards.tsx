import type { Stats } from "../api";

interface Props {
  stats: Stats;
}

function fmt(n: number, decimals = 2) {
  return n.toLocaleString("en-US", { maximumFractionDigits: decimals });
}

export function StatsCards({ stats }: Props) {
  const cards = [
    {
      label: "Eval Runs",
      value: stats.total_runs.toString(),
      sub: "total runs",
      color: "text-indigo-400",
    },
    {
      label: "Avg Pass Rate",
      value: `${fmt(stats.avg_pass_rate * 100, 1)}%`,
      sub: "across all runs",
      color: stats.avg_pass_rate >= 0.8 ? "text-emerald-400" : "text-amber-400",
    },
    {
      label: "Total Spend",
      value: `$${fmt(stats.total_cost_usd, 4)}`,
      sub: "USD",
      color: "text-zinc-100",
    },
    {
      label: "LLM Calls",
      value: stats.total_traces.toLocaleString(),
      sub: "traces captured",
      color: "text-violet-400",
    },
    {
      label: "Avg Latency",
      value: `${fmt(stats.avg_latency_ms, 0)}ms`,
      sub: "per call",
      color: "text-sky-400",
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      {cards.map((c) => (
        <div key={c.label} className="card">
          <div className={`stat-value ${c.color}`}>{c.value}</div>
          <div className="stat-label">{c.label}</div>
          <div className="text-xs text-zinc-600 mt-0.5">{c.sub}</div>
        </div>
      ))}
    </div>
  );
}
