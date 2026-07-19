import React, { useState, useRef } from "react";
import axiosInstance from "axios";
import LoadingPulse from "./components/LoadingPulse";
import ResultsPanel from "./components/ResultsPanel";
import ChatPanel from "./components/ChatPanel";

const API = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? "http://127.0.0.1:8000" : "");

export default function App() {
  const [loading, setLoading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  
  const [showFilters, setShowFilters] = useState(false);
  const [locationScope, setLocationScope] = useState("global");
  const [manualLocation, setManualLocation] = useState("");
  const [datePosted, setDatePosted] = useState("7d");
  const [workplaceOnSite, setWorkplaceOnSite] = useState(false);
  const [workplaceRemote, setWorkplaceRemote] = useState(true);
  const [workplaceHybrid, setWorkplaceHybrid] = useState(false);
  const [langSpanish, setLangSpanish] = useState(false);
  const [langEnglish, setLangEnglish] = useState(false);
  const [langAny, setLangAny] = useState(true);
  
  const fileInputRef = useRef(null);

  const handleToggleSpanish = () => {
    setLangSpanish((prev) => {
      const next = !prev;
      if (next) {
        setLangEnglish(false);
        setLangAny(false);
      } else {
        setLangAny(true);
      }
      return next;
    });
  };

  const handleToggleEnglish = () => {
    setLangEnglish((prev) => {
      const next = !prev;
      if (next) {
        setLangSpanish(false);
        setLangAny(false);
      } else {
        setLangAny(true);
      }
      return next;
    });
  };

  const handleToggleAny = () => {
    setLangAny(true);
    setLangSpanish(false);
    setLangEnglish(false);
  };

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
    formData.append("location_scope", locationScope);
    formData.append("date_posted", datePosted);
    
    // Determine job language to send
    let effectiveJobLang = "both";
    if (langSpanish && !langEnglish) {
      effectiveJobLang = "es";
    } else if (langEnglish && !langSpanish) {
      effectiveJobLang = "en";
    }
    formData.append("job_language", effectiveJobLang);
    
    if (locationScope === "manual" && manualLocation.trim()) {
      formData.append("manual_location", manualLocation.trim());
    }
    const wt = [];
    if (locationScope === "global") {
      wt.push("remoto");
    } else {
      if (workplaceOnSite) wt.push("presencial");
      if (workplaceRemote) wt.push("remoto");
      if (workplaceHybrid) wt.push("hibrido");
    }
    if (wt.length > 0) {
      formData.append("workplace_types", wt.join(","));
    }



    const uploadUrl = `${API}/api/upload-cv`;
    console.info("[UPLOAD] POST", uploadUrl);

    try {
      const res = await axiosInstance.post(uploadUrl, formData, {
        timeout: 240000 // 4 minutes timeout for parallel scraping + matching
      });
      setResult(res.data);
    } catch (err) {
      console.error("[UPLOAD] Request failed", {
        url: uploadUrl,
        code: err.code,
        message: err.message,
        status: err.response?.status,
        data: err.response?.data,
      });
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
              {/* Expandable Advanced Filters Accordion */}
              <div className="mb-5 border border-slate-800/80 rounded-2xl bg-slate-900/30 overflow-hidden backdrop-blur-sm">
                <button
                  type="button"
                  onClick={() => setShowFilters(!showFilters)}
                  className="w-full px-5 py-4 flex items-center justify-between text-sm font-semibold text-slate-200 hover:bg-slate-800/20 transition-colors"
                >
                  <span className="flex items-center gap-2">
                    <span className="text-violet-400">⚙️</span> Filtros de Búsqueda Avanzados (Opcional)
                  </span>
                  <span className={`transition-transform duration-300 ${showFilters ? "rotate-180" : ""}`}>
                    ▼
                  </span>
                </button>
                
                {showFilters && (
                  <div className="px-5 pb-5 pt-2 border-t border-slate-800/60 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                    {/* Ámbito de Ubicación */}
                    <div className="flex flex-col gap-1.5">
                      <label htmlFor="location-scope-select" className="text-slate-400 font-medium">Filtro Geográfico (Ubicación)</label>
                      <select
                        id="location-scope-select"
                        value={locationScope}
                        onChange={(e) => {
                          const scope = e.target.value;
                          setLocationScope(scope);
                          if (scope === "global") {
                            setWorkplaceRemote(true);
                            setWorkplaceOnSite(false);
                            setWorkplaceHybrid(false);
                          }
                        }}
                        className="bg-[#0e0e1a] border border-slate-800 rounded-lg px-3 py-2 text-slate-300 focus:outline-none focus:border-violet-500 transition-colors"
                      >
                        <option value="global">Todo el mundo (Global / Sin país)</option>
                        <option value="cv">Usar ubicación de mi CV</option>
                        <option value="manual">Especificar ubicación manualmente...</option>
                      </select>
                    </div>

                    {/* Date Posted */}
                    <div className="flex flex-col gap-1.5">
                      <label className="text-slate-400 font-medium">Fecha de Publicación</label>
                      <select
                        value={datePosted}
                        onChange={(e) => setDatePosted(e.target.value)}
                        className="bg-[#0e0e1a] border border-slate-800 rounded-lg px-3 py-2 text-slate-300 focus:outline-none focus:border-violet-500 transition-colors"
                      >
                        <option value="any">Cualquier momento</option>
                        <option value="7d">Última semana (7 días)</option>
                        <option value="24h">Últimas 24 horas</option>
                        <option value="30d">Último mes (30 días)</option>
                      </select>
                    </div>

                    {/* Job Language (Pills Selector) */}
                    <div className="flex flex-col gap-1.5 sm:col-span-2">
                      <label className="text-slate-400 font-medium">Idioma de la Oferta</label>
                      <div className="flex gap-2.5 mt-1">
                        <button
                          type="button"
                          onClick={handleToggleSpanish}
                          className={`flex-1 py-2 px-3 rounded-lg border text-center font-medium transition-all ${
                            langSpanish
                              ? "bg-violet-500/10 border-violet-500 text-violet-300 shadow-[0_0_10px_rgba(139,92,246,0.1)]"
                              : "bg-[#0e0e1a] border-slate-800/60 text-slate-500 hover:text-slate-350 hover:border-slate-700"
                          }`}
                        >
                          Español
                        </button>
                        <button
                          type="button"
                          onClick={handleToggleEnglish}
                          className={`flex-1 py-2 px-3 rounded-lg border text-center font-medium transition-all ${
                            langEnglish
                              ? "bg-violet-500/10 border-violet-500 text-violet-300 shadow-[0_0_10px_rgba(139,92,246,0.1)]"
                              : "bg-[#0e0e1a] border-slate-800/60 text-slate-500 hover:text-slate-350 hover:border-slate-700"
                          }`}
                        >
                          Inglés
                        </button>
                        <button
                          type="button"
                          onClick={handleToggleAny}
                          className={`flex-1 py-2 px-3 rounded-lg border text-center font-medium transition-all ${
                            langAny
                              ? "bg-violet-500/10 border-violet-500 text-violet-300 shadow-[0_0_10px_rgba(139,92,246,0.1)]"
                              : "bg-[#0e0e1a] border-slate-800/60 text-slate-500 hover:text-slate-350 hover:border-slate-700"
                          }`}
                        >
                          Cualquiera
                        </button>
                      </div>
                    </div>

                    {/* Manual Location Override (Only shown if scope is manual) */}
                    {locationScope === "manual" && (
                      <div className="flex flex-col gap-1.5 sm:col-span-2">
                        <label className="text-slate-400 font-medium">Ubicación Manual</label>
                        <input
                          type="text"
                          value={manualLocation}
                          onChange={(e) => setManualLocation(e.target.value)}
                          placeholder="Ej. Madrid, España / Colombia / London, UK"
                          className="bg-[#0e0e1a] border border-slate-800 rounded-lg px-3 py-2 text-slate-300 focus:outline-none focus:border-violet-500 transition-colors placeholder-slate-600 animate-fadeIn"
                        />
                      </div>
                    )}

                    {/* Workplace Modalidad (Workplace Type badging/pills) */}
                    <div className="flex flex-col gap-1.5 sm:col-span-2">
                      <label className="text-slate-400 font-medium flex items-center justify-between">
                        <span>Modalidad de Trabajo (Múltiple)</span>
                        {locationScope === "global" && (
                          <span className="text-[10px] text-violet-400/80 animate-pulse font-medium">Búsqueda global limitada a Remoto</span>
                        )}
                      </label>
                      <div className="flex gap-2.5 mt-1">
                        <button
                          type="button"
                          disabled={locationScope === "global"}
                          onClick={() => setWorkplaceOnSite(!workplaceOnSite)}
                          className={`flex-1 py-2 px-3 rounded-lg border text-center font-medium transition-all ${
                            locationScope === "global"
                              ? "bg-[#0c0c16]/30 border-slate-900/40 text-slate-700 cursor-not-allowed"
                              : workplaceOnSite
                              ? "bg-violet-500/10 border-violet-500 text-violet-300 shadow-[0_0_10px_rgba(139,92,246,0.1)]"
                              : "bg-[#0e0e1a] border-slate-800/60 text-slate-500 hover:text-slate-350 hover:border-slate-700"
                          }`}
                        >
                          Presencial
                        </button>
                        <button
                          type="button"
                          disabled={locationScope === "global"}
                          onClick={() => setWorkplaceHybrid(!workplaceHybrid)}
                          className={`flex-1 py-2 px-3 rounded-lg border text-center font-medium transition-all ${
                            locationScope === "global"
                              ? "bg-[#0c0c16]/30 border-slate-900/40 text-slate-700 cursor-not-allowed"
                              : workplaceHybrid
                              ? "bg-violet-500/10 border-violet-500 text-violet-300 shadow-[0_0_10px_rgba(139,92,246,0.1)]"
                              : "bg-[#0e0e1a] border-slate-800/60 text-slate-500 hover:text-slate-350 hover:border-slate-700"
                          }`}
                        >
                          Híbrido
                        </button>
                        <button
                          type="button"
                          disabled={locationScope === "global"}
                          onClick={() => setWorkplaceRemote(!workplaceRemote)}
                          className={`flex-1 py-2 px-3 rounded-lg border text-center font-medium transition-all ${
                            locationScope === "global"
                              ? "bg-[#0e0e1a]/80 border-violet-500/30 text-violet-400/80 cursor-not-allowed shadow-[0_0_10px_rgba(139,92,246,0.05)]"
                              : workplaceRemote
                              ? "bg-violet-500/10 border-violet-500 text-violet-300 shadow-[0_0_10px_rgba(139,92,246,0.1)]"
                              : "bg-[#0e0e1a] border-slate-800/60 text-slate-500 hover:text-slate-350 hover:border-slate-700"
                          }`}
                        >
                          Remoto
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
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
                data-testid="dropzone"
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
