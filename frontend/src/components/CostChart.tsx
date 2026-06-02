import { useEffect, useRef, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { DayCost } from "../api";

interface Props {
  data: DayCost[];
}

export function CostChart({ data }: Props) {
  const sorted = [...data].sort((a, b) => a.day.localeCompare(b.day));
  const containerRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(0);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect.width ?? 0;
      if (w > 0) setWidth(w);
    });
    ro.observe(el);
    // Measure immediately in case observer fires too late
    setWidth(el.getBoundingClientRect().width);
    return () => ro.disconnect();
  }, []);

  if (sorted.length === 0) {
    return (
      <div className="card flex items-center justify-center h-48 text-zinc-600 text-sm">
        No cost data yet — run an eval to see spending over time.
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-zinc-300 uppercase tracking-widest">
          Cost over time
        </h2>
        <span className="text-xs text-zinc-500">last 30 days</span>
      </div>
      <div ref={containerRef} style={{ width: "100%", height: 200 }}>
        {width > 0 && (
          <AreaChart
            width={width}
            height={200}
            data={sorted}
            margin={{ top: 4, right: 0, bottom: 0, left: 0 }}
          >
            <defs>
              <linearGradient id="costGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
            <XAxis
              dataKey="day"
              tick={{ fill: "#71717a", fontSize: 11 }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tick={{ fill: "#71717a", fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v: number) => `$${v.toFixed(4)}`}
            />
            <Tooltip
              contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", borderRadius: 8 }}
              labelStyle={{ color: "#a1a1aa" }}
              itemStyle={{ color: "#818cf8" }}
              formatter={(v: number) => [`$${v.toFixed(6)}`, "cost"]}
            />
            <Area
              type="monotone"
              dataKey="cost_usd"
              stroke="#6366f1"
              strokeWidth={2}
              fill="url(#costGrad)"
              isAnimationActive={false}
            />
          </AreaChart>
        )}
      </div>
    </div>
  );
}
