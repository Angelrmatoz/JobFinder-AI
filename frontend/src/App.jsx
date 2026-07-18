import { useState, useRef, useEffect } from "react";
import axiosInstance from "axios";

const API = "http://localhost:8000";

function Badge({ text, color = "slate" }) {
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
      className={`px-2 py-0.5 rounded text-xs border font-medium ${colors[color]}`}
    >
      {text}
    </span>
  );
}

function Section({ title, children }) {
  return (
    <div className="border border-slate-800 rounded-xl p-4 bg-slate-900/40">
      <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">
        {title}
      </h3>
      {children}
    </div>
  );
}

function ChatPanel({ data, API }) {
  const [chat, setChat] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat]);

  const send = async (override) => {
    const q = override || input;
    if (!q.trim() || loading) return;
    setInput("");
    setChat((p) => [...p, { role: "user", text: q }]);
    setLoading(true);
    try {
      const res = await axiosInstance.post(`${API}/api/chat`, {
        question: q,
        context: JSON.stringify(data),
      });
      setChat((p) => [...p, { role: "ai", text: res.data.answer }]);
    } catch {
      setChat((p) => [...p, { role: "ai", text: "Error — por favor intenta de nuevo." }]);
    } finally {
      setLoading(false);
    }
  };

  const suggestions = [
    "¿Qué vacante se adapta mejor a mi perfil?",
    "Redacta un mensaje para recursos humanos de la mejor oferta",
    "¿Qué habilidades debería mejorar según las vacantes?",
    "Ayúdame a redactar una carta de presentación para la vacante con mayor match",
  ];

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b border-slate-800 shrink-0">
        <p className="text-xs font-semibold text-slate-300">Asesor de Carrera IA</p>
        <p className="text-xs text-slate-600 mt-0.5">
          Pregunta sobre tu perfil o las vacantes encontradas
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2 min-h-0">
        {chat.length === 0 && (
          <div className="space-y-1.5">
            <p className="text-xs text-slate-600 px-1 mb-2">Preguntas sugeridas:</p>
            {suggestions.map((s) => (
              <button
                key={s}
                onClick={() => send(s)}
                className="w-full text-left text-xs px-3 py-2 rounded-lg bg-slate-800/60
                           text-slate-400 border border-slate-700/40 hover:border-slate-600
                           hover:text-slate-300 transition-all"
              >
                {s}
              </button>
            ))}
          </div>
        )}
        {chat.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[88%] px-3 py-2 rounded-lg text-xs leading-relaxed whitespace-pre-wrap ${
                msg.role === "user"
                  ? "bg-violet-600 text-white"
                  : "bg-slate-800 text-slate-300 border border-slate-700/50"
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-800 border border-slate-700/50 px-3 py-2.5 rounded-lg">
              <div className="flex gap-1 items-center">
                <span
                  className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce"
                  style={{ animationDelay: "0ms" }}
                />
                <span
                  className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce"
                  style={{ animationDelay: "150ms" }}
                />
                <span
                  className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce"
                  style={{ animationDelay: "300ms" }}
                />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="p-3 border-t border-slate-800 shrink-0">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder="Pregunta algo..."
            className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2
                       text-xs text-white placeholder-slate-600 focus:outline-none
                       focus:border-slate-600 transition-colors"
          />
          <button
            onClick={() => send()}
            disabled={loading || !input.trim()}
            className="px-3 py-2 rounded-lg bg-violet-600 hover:bg-violet-500
                       disabled:opacity-30 text-white text-xs font-bold transition-colors"
          >
            ↑
          </button>
        </div>
      </div>
    </div>
  );
}

function ResultsPanel({ data }) {
  const [activeTab, setActiveTab] = useState("vacantes");
  const profile = data.profile;
  const jobs = data.jobs || [];

  const getScoreColor = (score) => {
    if (score >= 8) return "emerald";
    if (score >= 6) return "amber";
    return "rose";
  };

  return (
    <div className="flex flex-col h-full">
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

function LoadingPulse({ message }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 gap-4">
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

export default function App() {
  const [loading, setLoading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  
  const fileInputRef = useRef(null);

  const loadingMessages = [
    "Leyendo y extrayendo texto del PDF...",
    "Interpretando CV con Gemma 4...",
    "Estructurando perfil profesional...",
    "Generando query optimizada para scraping...",
    "Buscando vacantes en LinkedIn en tiempo real...",
    "Buscando vacantes en Google Jobs...",
    "Analizando afinidad con inteligencia artificial...",
    "Guardando vacantes seleccionadas en Notion (Match > 7)...",
    "Consolidando resultados..."
  ];

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = async (file) => {
    if (file.type !== "application/pdf") {
      setError("Por favor, sube un archivo PDF válido.");
      return;
    }
    
    setLoading(true);
    setResult(null);
    setError(null);
    
    // Simulate cycling through progress messages
    let msgIdx = 0;
    setLoadingMsg(loadingMessages[0]);
    const interval = setInterval(() => {
      msgIdx = (msgIdx + 1) % loadingMessages.length;
      setLoadingMsg(loadingMessages[msgIdx]);
    }, 4500);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axiosInstance.post(`${API}/api/upload-cv`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        timeout: 240000 // 4 minutes timeout for parallel scraping + matching
      });
      setResult(res.data);
    } catch (err) {
      setError(
        err.response?.data?.detail || 
        "Hubo un error procesando el archivo. Asegúrate de configurar las APIs."
      );
    } finally {
      clearInterval(interval);
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen bg-[#080810] text-slate-300"
      style={{ fontFamily: "Inter, system-ui, sans-serif" }}
    >
      {/* Top bar */}
      <div className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-sm sticky top-0 z-20">
        <div className="max-w-screen-xl mx-auto px-5 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className="w-7 h-7 rounded-lg bg-gradient-to-br from-violet-500 to-cyan-500
                            flex items-center justify-center text-white font-bold text-xs"
            >
              J
            </div>
            <span className="font-semibold text-white text-sm">
              JobFinder <span className="text-violet-400">AI</span>
            </span>
            <span className="text-slate-700 text-xs hidden md:inline">
              — Auto Job Search & Matching
            </span>
          </div>
          <div className="flex items-center gap-4">
            {result && (
              <button
                onClick={() => {
                  setResult(null);
                  setError(null);
                }}
                className="text-xs text-slate-400 hover:text-slate-200 transition-colors"
              >
                ← Subir Otro CV
              </button>
            )}
            <div className="flex items-center gap-1.5 text-xs text-slate-700">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse inline-block" />
              Powered by Gemma & Apify
            </div>
          </div>
        </div>
      </div>

      {/* Landing / Drag & Drop Upload */}
      {!result && (
        <div className="max-w-xl mx-auto px-6 py-16">
          {!loading && (
            <div className="text-center mb-8">
              <div
                className="inline-flex items-center gap-2 px-3 py-1 rounded-full
                               bg-violet-500/10 border border-violet-500/20 text-violet-400
                               text-xs mb-5 font-medium"
              >
                Automatización de Búsqueda de Empleo
              </div>
              <h1 className="text-4xl font-black text-white mb-3 tracking-tight leading-tight">
                Encuentra tu próximo empleo
                <br />
                <span className="bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">
                  de forma automatizada
                </span>
              </h1>
              <p className="text-slate-500 text-sm leading-relaxed">
                Sube tu currículum en PDF. Nuestra IA interpretará tu perfil, buscará ofertas reales en LinkedIn y Google, evaluará su afinidad y guardará las mejores en Notion de manera automatizada.
              </p>
            </div>
          )}

          {loading ? (
            <div className="border border-slate-800 rounded-2xl bg-slate-900/40">
              <LoadingPulse message={loadingMsg} />
            </div>
          ) : (
            <>
              <div
                onDragEnter={handleDrag}
                onDragOver={handleDrag}
                onDragLeave={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current.click()}
                className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-300 ${
                  dragActive
                    ? "border-violet-500 bg-violet-500/5 shadow-[0_0_20px_rgba(139,92,246,0.15)]"
                    : "border-slate-800 bg-slate-900/20 hover:border-slate-700 hover:bg-slate-900/30"
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <div className="flex flex-col items-center gap-4">
                  <div className="w-14 h-14 rounded-full bg-gradient-to-br from-violet-500 to-cyan-500 flex items-center justify-center text-white text-lg font-bold">
                    ↑
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white mb-1">
                      Arrastra tu CV en PDF aquí
                    </h3>
                    <p className="text-xs text-slate-500">
                      o haz clic para explorar tus archivos
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex justify-center gap-5 mt-8 text-xs text-slate-700">
                <span>✓ Lectura de PDF</span>
                <span>✓ Conexión LinkedIn & Google</span>
                <span>✓ Filtro Cognitivo Gemma</span>
                <span>✓ Auto-Guardado en Notion</span>
              </div>
            </>
          )}

          {error && (
            <div className="mt-4 border border-rose-800/40 bg-rose-950/20 rounded-xl p-4 text-rose-400 text-sm">
              ❌ {error}
            </div>
          )}
        </div>
      )}

      {/* Two-column results layout */}
      {result && (
        <div
          className="max-w-screen-xl mx-auto px-4 pb-4 pt-3"
          style={{ height: "calc(100vh - 49px)" }}
        >
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 h-full">
            {/* LEFT — Vacancies & profile */}
            <div
              className="lg:col-span-2 border border-slate-800 rounded-xl
                            bg-slate-900/20 overflow-hidden flex flex-col"
            >
              <ResultsPanel data={result} />
            </div>

            {/* RIGHT — Career Coach chat */}
            <div
              className="border border-slate-800 rounded-xl
                            bg-slate-900/20 overflow-hidden flex flex-col"
            >
              <ChatPanel data={result} API={API} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
