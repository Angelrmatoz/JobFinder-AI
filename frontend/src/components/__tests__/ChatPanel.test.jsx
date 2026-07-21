import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import ChatPanel from "../ChatPanel";

// Mock axios module
vi.mock("axios", () => {
  return {
    default: {
      post: vi.fn().mockResolvedValue({ data: { answer: "Respuesta de la IA" } })
    }
  };
});

import axiosInstance from "axios";

describe("ChatPanel Component", () => {
  it("renders carrier advisor info and suggestions list", () => {
    render(<ChatPanel data={{}} API="http://localhost:8000" />);
    expect(screen.getByText("Asesor de Carrera IA")).toBeInTheDocument();
    expect(screen.getByTestId("suggestions-list")).toBeInTheDocument();
  });

  it("sends user message and renders AI response from mocked API", async () => {
    render(<ChatPanel data={{}} API="http://localhost:8000" />);
    
    const input = screen.getByPlaceholderText("Pregunta algo...");
    const sendButton = screen.getByRole("button", { name: "↑" });
    
    // Simulate typing and sending
    fireEvent.change(input, { target: { value: "Hola, ¿cómo estás?" } });
    fireEvent.click(sendButton);
    
    // Check that user message is in the document
    expect(screen.getByText("Hola, ¿cómo estás?")).toBeInTheDocument();
    
    // Wait for mock API response to be rendered
    await waitFor(() => {
      expect(screen.getByText("Respuesta de la IA")).toBeInTheDocument();
    });
    
    expect(axiosInstance.post).toHaveBeenCalledWith(
      "http://localhost:8000/api/chat",
      expect.objectContaining({ question: "Hola, ¿cómo estás?" })
    );
  });

  it("sends message when Enter key is pressed", async () => {
    render(<ChatPanel data={{}} API="http://localhost:8000" />);

    const input = screen.getByPlaceholderText("Pregunta algo...");

    fireEvent.change(input, { target: { value: "Pregunta via Enter" } });
    fireEvent.keyDown(input, { key: "Enter", code: "Enter" });

    expect(screen.getByText("Pregunta via Enter")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Respuesta de la IA")).toBeInTheDocument();
    });
  });
});
