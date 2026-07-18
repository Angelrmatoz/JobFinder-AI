import React, { useState, useRef } from "react";
import axiosInstance from "axios";
import LoadingPulse from "./components/LoadingPulse";
import ResultsPanel from "./components/ResultsPanel";
import ChatPanel from "./components/ChatPanel";

const API = "http://localhost:8000";

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
