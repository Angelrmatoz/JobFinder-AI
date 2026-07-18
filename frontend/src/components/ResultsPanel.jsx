import React, { useState } from "react";
import Badge from "./Badge";
import Section from "./Section";

export default function ResultsPanel({ data }) {
  const [activeTab, setActiveTab] = useState("vacantes");
  const profile = data?.profile || {};
  const jobs = data?.jobs || [];

  const getScoreColor = (score) => {
    if (score >= 8) return "emerald";
    if (score >= 6) return "amber";
    return "rose";
  };

  return (
    <div className="flex flex-col h-full" data-testid="results-panel">
      {/* Candidate header */}
      <div className="px-5 py-4 border-b border-slate-800 shrink-0">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-2.5">
            <div
              className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-cyan-500
                            flex items-center justify-center text-white text-sm font-bold shrink-0"
            >
              {profile.name?.[0]?.toUpperCase() || "C"}
            </div>
            <div>
              <h2 className="text-base font-bold text-white leading-none">
                {profile.name || "Candidato"}
              </h2>
              <span className="text-xs text-slate-600">
                {profile.email || "Email no extraído"}
              </span>
            </div>
          </div>
          <div className="flex flex-wrap gap-1.5">
            <Badge text={`${jobs.length} vacantes`} color="cyan" />
            <Badge text="Perfil Extraído" color="violet" />
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 px-5 shrink-0">
        <button
          onClick={() => setActiveTab("vacantes")}
          className={`text-xs py-2.5 px-3 mr-2 border-b-2 transition-colors font-medium ${
            activeTab === "vacantes"
              ? "border-violet-500 text-white"
              : "border-transparent text-slate-600 hover:text-slate-400"
          }`}
        >
          Vacantes Encontradas
        </button>
        <button
          onClick={() => setActiveTab("perfil")}
          className={`text-xs py-2.5 px-3 mr-2 border-b-2 transition-colors font-medium ${
            activeTab === "perfil"
              ? "border-violet-500 text-white"
              : "border-transparent text-slate-600 hover:text-slate-400"
          }`}
        >
          Perfil Extraído
        </button>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto p-5 space-y-3 min-h-0">
        {/* PROFILE TAB */}
        {activeTab === "perfil" && (
          <>
            <Section title="Resumen Profesional">
              <p className="text-sm text-slate-300 leading-relaxed">
                {profile.experience_summary}
              </p>
            </Section>

            <Section title="Habilidades Técnicas / Soft Skills">
              <div className="flex flex-wrap gap-1.5">
                {(profile.skills || []).map((t, i) => (
                  <Badge key={i} text={t} color="violet" />
                ))}
              </div>
            </Section>

            <Section title="Roles de Interés">
              <div className="flex flex-wrap gap-1.5">
                {(profile.target_roles || []).map((c, i) => (
                  <Badge key={i} text={c} color="cyan" />
                ))}
              </div>
            </Section>

            <Section title="Query de Búsqueda de Empleo">
              <p className="text-sm font-mono text-violet-400 bg-violet-950/20 border border-violet-900/30 p-3 rounded-lg">
                "{profile.search_query}"
              </p>
            </Section>
          </>
        )}

        {/* VACANCIES TAB */}
        {activeTab === "vacantes" && (
          <div className="space-y-4">
            {jobs.length === 0 ? (
              <div className="text-center py-10 text-slate-500 text-sm">
                No se encontraron vacantes que coincidan.
              </div>
            ) : (
              jobs.map((job, i) => (
                <div
                  key={i}
                  className="border border-slate-800/80 rounded-xl p-4 bg-slate-900/20 hover:border-slate-700/80 transition-all flex flex-col gap-3"
                  data-testid="job-item"
                >
                  <div className="flex justify-between items-start gap-2">
                    <div>
                      <h4 className="text-sm font-bold text-white leading-tight">
                        {job.title}
                      </h4>
                      <p className="text-xs text-slate-400 mt-1">
                        {job.company} — <span className="text-slate-500">{job.location}</span>
                      </p>
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      {job.saved_to_notion && (
                        <span className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded text-[10px] font-bold">
                          ✓ Notion
                        </span>
                      )}
                      <Badge
                        text={`Match: ${job.match_score}/10`}
                        color={getScoreColor(job.match_score)}
                      />
                    </div>
                  </div>

                  {job.description && (
                    <p className="text-xs text-slate-500 line-clamp-2">
                      {job.description}
                    </p>
                  )}

                  {job.apply_tip && (
                    <div className="bg-violet-950/20 border border-violet-900/30 rounded-lg p-2.5 text-xs text-violet-300">
                      <span className="font-bold block text-[10px] text-violet-400 uppercase tracking-wider mb-1">
                        Consejo para Aplicar
                      </span>
                      {job.apply_tip}
                    </div>
                  )}

                  <div className="flex justify-end mt-1">
                    <a
                      href={job.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1.5 bg-slate-850 hover:bg-slate-700 text-white rounded-lg text-xs font-semibold border border-slate-750 transition-colors flex items-center gap-1"
                    >
                      Ver Oferta ↗
                    </a>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
