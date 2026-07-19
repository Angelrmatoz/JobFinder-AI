import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import App from "../App";

describe("Frontend Filters UI Interaction", () => {
  it("debe tener seleccionado 'Todo el mundo (Global)' por defecto y deshabilitar Presencial/Híbrido", () => {
    render(<App />);

    // Expandir el acordeón de filtros
    const toggleFiltersBtn = screen.getByRole("button", { name: /Filtros de Búsqueda Avanzados/i });
    fireEvent.click(toggleFiltersBtn);

    // Verificar que el select tenga el valor 'global'
    const selectLocation = screen.getByLabelText(/Filtro Geográfico/i);
    expect(selectLocation.value).toBe("global");

    // En global, la modalidad 'Presencial' y 'Híbrido' deben estar desactivadas (disabled)
    const btnPresencial = screen.getByRole("button", { name: "Presencial" });
    const btnHibrido = screen.getByRole("button", { name: "Híbrido" });
    const btnRemoto = screen.getByRole("button", { name: "Remoto" });

    expect(btnPresencial).toBeDisabled();
    expect(btnHibrido).toBeDisabled();
    expect(btnRemoto).toBeDisabled(); // Remoto también está forzado y deshabilitado

    // Input de ubicación manual no debe existir en el DOM en modo global
    expect(screen.queryByPlaceholderText(/Ej. Madrid, España/i)).not.toBeInTheDocument();
  });

  it("debe habilitar Presencial/Híbrido e input manual al cambiar a 'Especificar ubicación manualmente...'", () => {
    render(<App />);

    // Expandir el acordeón
    const toggleFiltersBtn = screen.getByRole("button", { name: /Filtros de Búsqueda Avanzados/i });
    fireEvent.click(toggleFiltersBtn);

    const selectLocation = screen.getByLabelText(/Filtro Geográfico/i);
    
    // Cambiar a manual
    fireEvent.change(selectLocation, { target: { value: "manual" } });
    expect(selectLocation.value).toBe("manual");

    // Debe aparecer el input de ubicación manual
    const inputManual = screen.getByPlaceholderText(/Ej. Madrid, España/i);
    expect(inputManual).toBeInTheDocument();

    // Las modalidades deben estar habilitadas
    const btnPresencial = screen.getByRole("button", { name: "Presencial" });
    const btnHibrido = screen.getByRole("button", { name: "Híbrido" });
    const btnRemoto = screen.getByRole("button", { name: "Remoto" });

    expect(btnPresencial).not.toBeDisabled();
    expect(btnHibrido).not.toBeDisabled();
    expect(btnRemoto).not.toBeDisabled();
  });

  it("debe habilitar modalidades pero ocultar input manual al cambiar a 'Usar ubicación de mi CV'", () => {
    render(<App />);

    // Expandir acordeón
    const toggleFiltersBtn = screen.getByRole("button", { name: /Filtros de Búsqueda Avanzados/i });
    fireEvent.click(toggleFiltersBtn);

    const selectLocation = screen.getByLabelText(/Filtro Geográfico/i);
    
    // Cambiar a cv
    fireEvent.change(selectLocation, { target: { value: "cv" } });
    expect(selectLocation.value).toBe("cv");

    // No debe mostrar el input de ubicación manual
    expect(screen.queryByPlaceholderText(/Ej. Madrid, España/i)).not.toBeInTheDocument();

    // Las modalidades deben estar habilitadas
    const btnPresencial = screen.getByRole("button", { name: "Presencial" });
    const btnHibrido = screen.getByRole("button", { name: "Híbrido" });
    const btnRemoto = screen.getByRole("button", { name: "Remoto" });

    expect(btnPresencial).not.toBeDisabled();
    expect(btnHibrido).not.toBeDisabled();
    expect(btnRemoto).not.toBeDisabled();
  });
});
