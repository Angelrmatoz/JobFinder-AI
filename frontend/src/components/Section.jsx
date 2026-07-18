import React from "react";

export default function Section({ title, children }) {
  return (
    <div className="border border-slate-800 rounded-xl p-4 bg-slate-900/40" data-testid="section">
      <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">
        {title}
      </h3>
      {children}
    </div>
  );
}
