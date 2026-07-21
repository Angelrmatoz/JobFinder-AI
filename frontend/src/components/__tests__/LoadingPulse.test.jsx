import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import LoadingPulse from "../LoadingPulse";

describe("LoadingPulse Component", () => {
  it("renders loading message", () => {
    render(<LoadingPulse message="Procesando tu CV..." />);
    expect(screen.getByTestId("loading-pulse")).toBeInTheDocument();
    expect(screen.getByText("Procesando tu CV...")).toBeInTheDocument();
  });

  it("renders different messages correctly", () => {
    const { rerender } = render(<LoadingPulse message="Buscando vacantes..." />);
    expect(screen.getByText("Buscando vacantes...")).toBeInTheDocument();

    rerender(<LoadingPulse message="Evaluando afinidad..." />);
    expect(screen.getByText("Evaluando afinidad...")).toBeInTheDocument();
  });

  it("renders spinner elements inside container", () => {
    render(<LoadingPulse message="Cargando..." />);
    const container = screen.getByTestId("loading-pulse");
    // Spinner divs are children of the container
    expect(container.querySelector(".animate-spin")).not.toBeNull();
  });
});
