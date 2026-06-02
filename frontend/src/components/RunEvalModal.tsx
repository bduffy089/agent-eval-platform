import { useState } from "react";
import { api } from "../api";

interface Props {
  onClose: () => void;
  onDone: () => void;
}

export function RunEvalModal({ onClose, onDone }: Props) {
  const [dataset, setDataset] = useState("json_extraction");
  const [provider, setProvider] = useState("claude");
  const [model, setModel] = useState("claude-haiku-4-5");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setLoading(true);
    setError(null);
    try {
      await api.createRun(dataset, provider, model);
      onDone();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 w-full max-w-sm space-y-4">
        <h3 className="font-semibold text-zinc-100">Run Eval</h3>

        <div>
          <label className="text-xs text-zinc-500 uppercase tracking-widest">Dataset</label>
          <input
            value={dataset}
            onChange={(e) => setDataset(e.target.value)}
            className="mt-1 w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 font-mono focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div>
          <label className="text-xs text-zinc-500 uppercase tracking-widest">Provider</label>
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            className="mt-1 w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:border-indigo-500"
          >
            <option value="claude">Claude</option>
            <option value="openai">OpenAI</option>
          </select>
        </div>

        <div>
          <label className="text-xs text-zinc-500 uppercase tracking-widest">Model</label>
          <input
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="mt-1 w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 font-mono focus:outline-none focus:border-indigo-500"
          />
        </div>

        {error && (
          <div className="text-xs text-red-400 bg-red-950/30 border border-red-800/40 rounded-lg px-3 py-2">
            {error}
          </div>
        )}

        <div className="flex gap-2 pt-1">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 rounded-lg border border-zinc-700 text-sm text-zinc-400 hover:text-zinc-200 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={submit}
            disabled={loading}
            className="flex-1 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-sm font-medium transition-colors"
          >
            {loading ? "Running…" : "Run"}
          </button>
        </div>
      </div>
    </div>
  );
}
