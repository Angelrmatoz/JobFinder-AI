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
    const btnCualquierModalidad = screen.getByRole("button", { name: "Cualquier modalidad" });

    expect(btnPresencial).toBeDisabled();
    expect(btnHibrido).toBeDisabled();
    expect(btnRemoto).toBeDisabled(); // Remoto también está forzado y deshabilitado
    expect(btnCualquierModalidad).toBeDisabled(); // Global no permite elegir modalidad

    // Solo deben existir las dos opciones de ubicación: global y CV
    const options = Array.from(selectLocation.options).map((option) => option.value);
    expect(options).toEqual(["global", "cv"]);
    expect(screen.queryByTestId("manual-location-input")).not.toBeInTheDocument();
  });

  it("no debe ofrecer la opción de ubicación manual", () => {
    render(<App />);

    // Expandir el acordeón
    const toggleFiltersBtn = screen.getByRole("button", { name: /Filtros de Búsqueda Avanzados/i });
    fireEvent.click(toggleFiltersBtn);

    const selectLocation = screen.getByLabelText(/Filtro Geográfico/i);
    expect(screen.queryByRole("option", { name: /Especificar ubicación manualmente/i })).not.toBeInTheDocument();
    expect(Array.from(selectLocation.options)).toHaveLength(2);
    expect(screen.queryByTestId("manual-location-input")).not.toBeInTheDocument();
  });

  it("debe habilitar modalidades al cambiar a 'Usar ubicación de mi CV'", () => {
    render(<App />);

    // Expandir acordeón
    const toggleFiltersBtn = screen.getByRole("button", { name: /Filtros de Búsqueda Avanzados/i });
    fireEvent.click(toggleFiltersBtn);

    const selectLocation = screen.getByLabelText(/Filtro Geográfico/i);
    
    // Cambiar a cv
    fireEvent.change(selectLocation, { target: { value: "cv" } });
    expect(selectLocation.value).toBe("cv");

    // Las modalidades deben estar habilitadas
    const btnPresencial = screen.getByRole("button", { name: "Presencial" });
    const btnHibrido = screen.getByRole("button", { name: "Híbrido" });
    const btnRemoto = screen.getByRole("button", { name: "Remoto" });
    const btnCualquierModalidad = screen.getByRole("button", { name: "Cualquier modalidad" });

    expect(btnPresencial).not.toBeDisabled();
    expect(btnHibrido).not.toBeDisabled();
    expect(btnRemoto).not.toBeDisabled();
    expect(btnCualquierModalidad).not.toBeDisabled();
    // El input manual ya no existe en ningún modo
    expect(screen.queryByTestId("manual-location-input")).not.toBeInTheDocument();
  });

  it("'Cualquier modalidad' limpia las modalidades y se desactiva al elegir una específica", () => {
    render(<App />);

    const toggleFiltersBtn = screen.getByRole("button", { name: /Filtros de Búsqueda Avanzados/i });
    fireEvent.click(toggleFiltersBtn);

    const selectLocation = screen.getByLabelText(/Filtro Geográfico/i);
    fireEvent.change(selectLocation, { target: { value: "cv" } });

    const btnPresencial = screen.getByRole("button", { name: "Presencial" });
    const btnHibrido = screen.getByRole("button", { name: "Híbrido" });
    const btnRemoto = screen.getByRole("button", { name: "Remoto" });
    const btnCualquierModalidad = screen.getByRole("button", { name: "Cualquier modalidad" });

    // Remoto está activo por defecto; "Cualquier modalidad" no
    expect(btnRemoto).toHaveClass("bg-violet-500/10");
    expect(btnCualquierModalidad).not.toHaveClass("bg-violet-500/10");

    // Al elegir cualquier modalidad se limpian las específicas
    fireEvent.click(btnCualquierModalidad);
    expect(btnCualquierModalidad).toHaveClass("bg-violet-500/10");
    expect(btnPresencial).not.toHaveClass("bg-violet-500/10");
    expect(btnHibrido).not.toHaveClass("bg-violet-500/10");
    expect(btnRemoto).not.toHaveClass("bg-violet-500/10");

    // Al elegir una específica, "Cualquier modalidad" se desactiva
    fireEvent.click(btnHibrido);
    expect(btnHibrido).toHaveClass("bg-violet-500/10");
    expect(btnCualquierModalidad).not.toHaveClass("bg-violet-500/10");
  });

  it("debe permitir selección exclusiva de Español e Inglés y colapsar a Cualquiera si se desmarcan", () => {
    render(<App />);

    // Expandir acordeón
    const toggleFiltersBtn = screen.getByRole("button", { name: /Filtros de Búsqueda Avanzados/i });
    fireEvent.click(toggleFiltersBtn);

    const btnEspanol = screen.getByRole("button", { name: "Español" });
    const btnIngles = screen.getByRole("button", { name: "Inglés" });
    const btnCualquiera = screen.getByRole("button", { name: "Cualquiera" });

    // Por defecto 'Cualquiera' es activo
    expect(btnCualquiera).toHaveClass("bg-violet-500/10");
    expect(btnEspanol).toHaveClass("bg-[#0e0e1a]");
    expect(btnIngles).toHaveClass("bg-[#0e0e1a]");

    // Clic en Español -> Español activo, otros inactivos
    fireEvent.click(btnEspanol);
    expect(btnEspanol).toHaveClass("bg-violet-500/10");
    expect(btnIngles).toHaveClass("bg-[#0e0e1a]");
    expect(btnCualquiera).toHaveClass("bg-[#0e0e1a]");

    // Clic en Inglés -> Inglés activo, Español inactivo (exclusión mutua)
    fireEvent.click(btnIngles);
    expect(btnIngles).toHaveClass("bg-violet-500/10");
    expect(btnEspanol).toHaveClass("bg-[#0e0e1a]");
    expect(btnCualquiera).toHaveClass("bg-[#0e0e1a]");

    // Clic en Inglés de nuevo -> Todos inactivos, vuelve a Cualquiera
    fireEvent.click(btnIngles);
    expect(btnCualquiera).toHaveClass("bg-violet-500/10");
    expect(btnEspanol).toHaveClass("bg-[#0e0e1a]");
    expect(btnIngles).toHaveClass("bg-[#0e0e1a]");
  });
});
