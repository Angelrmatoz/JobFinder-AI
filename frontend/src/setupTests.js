import "@testing-library/jest-dom";

// Mock scrollIntoView for jsdom compatibility in Vitest
if (typeof window !== "undefined" && window.HTMLElement) {
  window.HTMLElement.prototype.scrollIntoView = function() {};
}
