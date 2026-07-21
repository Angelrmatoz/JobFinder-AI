import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import Section from "../Section";

describe("Section Component", () => {
  it("renders title and children", () => {
    render(
      <Section title="Habilidades">
        <span>React</span>
      </Section>
    );
    expect(screen.getByTestId("section")).toBeInTheDocument();
    expect(screen.getByText("Habilidades")).toBeInTheDocument();
    expect(screen.getByText("React")).toBeInTheDocument();
  });

  it("renders without children", () => {
    render(<Section title="Sin contenido" />);
    expect(screen.getByText("Sin contenido")).toBeInTheDocument();
  });

  it("applies uppercase tracking class to title", () => {
    render(<Section title="Test" />);
    const heading = screen.getByText("Test");
    expect(heading.className).toContain("uppercase");
    expect(heading.className).toContain("tracking-widest");
  });
});
