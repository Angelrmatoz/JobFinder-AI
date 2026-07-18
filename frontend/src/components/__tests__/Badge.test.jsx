import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import Badge from "../Badge";

describe("Badge Component", () => {
  it("renders text prop correctly", () => {
    render(<Badge text="React" color="violet" />);
    const badgeElement = screen.getByTestId("badge");
    expect(badgeElement).toBeInTheDocument();
    expect(badgeElement).toHaveTextContent("React");
  });

  it("applies the correct styling class depending on color prop", () => {
    render(<Badge text="React" color="violet" />);
    const badgeElement = screen.getByTestId("badge");
    expect(badgeElement).toHaveClass("bg-violet-500/15");
  });

  it("defaults to slate style if color is invalid or not provided", () => {
    render(<Badge text="Vite" />);
    const badgeElement = screen.getByTestId("badge");
    expect(badgeElement).toHaveClass("bg-slate-800");
  });
});
