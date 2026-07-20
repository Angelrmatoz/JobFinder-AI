import React, { useState, useRef, useEffect } from "react";
import axiosInstance from "axios";

function formatMessage(text) {
  if (!text) return "";
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={index} className="font-bold text-slate-100">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return part;
  });
}

export default function ChatPanel({ data, API }) {
  const [chat, setChat] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    if (bottomRef.current?.scrollIntoView) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
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
    <div className="flex flex-col h-full" data-testid="chat-panel">
      <div className="px-4 py-3 border-b border-slate-800 shrink-0">
        <p className="text-xs font-semibold text-slate-300">Asesor de Carrera IA</p>
        <p className="text-xs text-slate-600 mt-0.5">
          Pregunta sobre tu perfil o las vacantes encontradas
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2 min-h-0">
        {chat.length === 0 && (
          <div className="space-y-1.5" data-testid="suggestions-list">
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
            data-testid="chat-message"
          >
            <div
              className={`max-w-[88%] px-3 py-2 rounded-lg text-xs leading-relaxed whitespace-pre-wrap ${
                msg.role === "user"
                  ? "bg-violet-600 text-white"
                  : "bg-slate-800 text-slate-300 border border-slate-700/50"
              }`}
            >
              {formatMessage(msg.text)}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start" data-testid="chat-loading">
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
