import React from "react";

export default function LoadingPulse({ message }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 gap-4" data-testid="loading-pulse">
      <div className="relative w-10 h-10">
        <div className="absolute inset-0 rounded-full border-2 border-violet-500 border-t-transparent animate-spin" />
        <div
          className="absolute inset-1.5 rounded-full border-2 border-cyan-400 border-b-transparent animate-spin"
          style={{ animationDirection: "reverse" }}
        />
      </div>
      <p className="text-slate-300 text-xs font-medium animate-pulse">{message}</p>
    </div>
  );
}
