const BASE = "/api";

export interface Stats {
  total_runs: number;
  avg_pass_rate: number;
  total_cost_usd: number;
  total_traces: number;
  avg_latency_ms: number;
}

export interface DayCost {
  day: string;
  cost_usd: number;
  calls: number;
  input_tokens: number;
  output_tokens: number;
  cache_read_tokens: number;
}

export interface DayRuns {
  day: string;
  runs: number;
  avg_pass_rate: number;
}

export interface EvalRun {
  id: string;
  created_at: string;
  dataset_name: string;
  provider: string;
  model: string;
  total_cases: number;
  passed_cases: number;
  pass_rate: number;
  total_cost_usd: number;
  total_latency_ms: number;
}

export interface CaseResult {
  case_id: string;
  passed: boolean;
  output: string | null;
  scores: { scorer: string; passed: boolean; score: number; reason: string | null }[];
  cost_usd: number;
  latency_ms: number;
}

export interface EvalRunDetail extends EvalRun {
  cases: CaseResult[];
}

export interface Trace {
  id: string;
  created_at: string;
  agent_name: string | null;
  run_id: string | null;
  provider: string;
  model: string;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  cache_read_tokens: number;
  cache_write_tokens: number;
  cost_usd: number;
}

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json() as Promise<T>;
}

export const api = {
  stats: () => get<Stats>("/dashboard/stats"),
  costOverTime: (days = 30) => get<DayCost[]>(`/dashboard/cost-over-time?days=${days}`),
  runsOverTime: (days = 30) => get<DayRuns[]>(`/dashboard/runs-over-time?days=${days}`),
  listRuns: (limit = 20) => get<EvalRun[]>(`/runs?limit=${limit}`),
  getRun: (id: string) => get<EvalRunDetail>(`/runs/${id}`),
  listTraces: (limit = 50) => get<Trace[]>(`/traces?limit=${limit}`),
  createRun: (dataset: string, provider: string, model: string) =>
    post<{ run_id: string; pass_rate: number; total_cost_usd: number }>("/runs", {
      dataset,
      provider,
      model,
    }),
  marketResearch: (topic: string, model = "claude-sonnet-4-6") =>
    post<Record<string, unknown>>("/agents/market-research", { topic, model }),
};
