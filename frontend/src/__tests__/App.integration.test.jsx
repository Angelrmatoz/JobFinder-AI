import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import App from "../App";

// Mock del cliente axios
vi.mock("axios", () => {
  return {
    default: {
      post: vi.fn()
    }
  };
});

import axiosInstance from "axios";

const mockApiResponse = {
  profile: {
    name: "María Gómez",
    email: "maria@example.com",
    skills: ["Python", "Machine Learning"],
    experience_summary: "Científica de datos con 2 años de experiencia.",
    target_roles: ["Data Scientist"],
    search_query: "Data Scientist junior"
  },
  jobs: [
    {
      title: "Data Scientist",
      company: "DataCorp",
      location: "Remote",
      link: "https://example.com/apply-ds",
      description: "Buscamos científico de datos.",
      match_score: 9,
      apply_tip: "Tip de machine learning.",
      saved_to_notion: true
    }
  ]
};

describe("Integración Frontend - Flujo Completo App", () => {
  it("debe ejecutar el flujo completo: subida, carga y renderizado de resultados", async () => {
    // Configurar el mock para retornar la respuesta exitosa
    axiosInstance.post.mockResolvedValue({ data: mockApiResponse });

    const { container } = render(<App />);

    // 1. Estado inicial: Se muestra la zona de arrastre (dropzone)
    expect(screen.getByTestId("dropzone")).toBeInTheDocument();
    expect(screen.queryByTestId("results-panel")).not.toBeInTheDocument();

    // 2. Obtener el input de archivos oculto y simular la subida del PDF
    const file = new File(["dummy pdf content"], "mi_cv.pdf", { type: "application/pdf" });
    const fileInput = container.querySelector('input[type="file"]');
    
    // Disparar evento de cambio de archivo
    fireEvent.change(fileInput, { target: { files: [file] } });

    // 3. Verificar estado de carga: Se muestra LoadingPulse con mensaje inicial
    expect(screen.getByTestId("loading-pulse")).toBeInTheDocument();
    expect(screen.getByText("Leyendo y extrayendo texto del PDF...")).toBeInTheDocument();

    // 4. Esperar que se resuelva la petición y aparezca el panel de resultados
    await waitFor(() => {
      expect(screen.getByTestId("results-panel")).toBeInTheDocument();
    }, { timeout: 5000 });

    // 5. Validar que la información del candidato e interfaces se hayan integrado
    expect(screen.getByText("María Gómez")).toBeInTheDocument();
    expect(screen.getByText("maria@example.com")).toBeInTheDocument();
    
    // Validar vacante en ResultsPanel
    expect(screen.getByText("Data Scientist")).toBeInTheDocument();
    expect(screen.getByText("DataCorp —")).toBeInTheDocument();

    // Validar existencia del ChatPanel integrado
    expect(screen.getByTestId("chat-panel")).toBeInTheDocument();
  });
});
