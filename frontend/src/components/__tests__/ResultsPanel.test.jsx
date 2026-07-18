import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import ResultsPanel from "../ResultsPanel";

const mockData = {
  profile: {
    name: "Alex Doe",
    email: "alex.doe@example.com",
    skills: ["JavaScript", "HTML", "CSS"],
    experience_summary: "Desarrollador frontend con experiencia en React.",
    target_roles: ["Frontend Developer"],
    search_query: "React developer remote"
  },
  jobs: [
    {
      title: "Frontend Developer",
      company: "Innovate Inc",
      location: "Remote",
      link: "https://example.com/apply",
      description: "Buscamos un programador React.",
      match_score: 9,
      apply_tip: "Tip de ejemplo.",
      saved_to_notion: true
    }
  ]
};

describe("ResultsPanel Component", () => {
  it("renders candidate name and email", () => {
    render(<ResultsPanel data={mockData} />);
    expect(screen.getByText("Alex Doe")).toBeInTheDocument();
    expect(screen.getByText("alex.doe@example.com")).toBeInTheDocument();
  });

  it("renders job vacancy items by default on the vacancies tab", () => {
    render(<ResultsPanel data={mockData} />);
    expect(screen.getByText("Frontend Developer")).toBeInTheDocument();
    expect(screen.getByText("Innovate Inc —")).toBeInTheDocument();
    expect(screen.getByText("✓ Notion")).toBeInTheDocument();
  });

  it("switches tabs and displays profile overview details when clicked", () => {
    render(<ResultsPanel data={mockData} />);
    
    // Switch to profile tab
    const profileTabButton = screen.getByRole("button", { name: "Perfil Extraído" });
    fireEvent.click(profileTabButton);
    
    expect(screen.getByText("Desarrollador frontend con experiencia en React.")).toBeInTheDocument();
    expect(screen.getByText("JavaScript")).toBeInTheDocument();
  });
});
