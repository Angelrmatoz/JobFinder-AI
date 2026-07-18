import React from "react";

export default function Badge({ text, color = "slate" }) {
  const colors = {
    slate: "bg-slate-800 text-slate-300 border-slate-700",
    violet: "bg-violet-500/15 text-violet-300 border-violet-500/25",
    cyan: "bg-cyan-500/15 text-cyan-300 border-cyan-500/25",
    emerald: "bg-emerald-500/15 text-emerald-300 border-emerald-500/25",
    rose: "bg-rose-500/15 text-rose-300 border-rose-500/25",
    amber: "bg-amber-500/15 text-amber-300 border-amber-500/25",
  };
  return (
    <span
      className={`px-2 py-0.5 rounded text-xs border font-medium ${colors[color] || colors.slate}`}
      data-testid="badge"
    >
      {text}
    </span>
  );
}
