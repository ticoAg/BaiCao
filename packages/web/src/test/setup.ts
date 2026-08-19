import "@testing-library/jest-dom/vitest";
import { beforeEach, vi } from "vitest";
import { notificationApi } from "../services/api";

beforeEach(() => {
  vi.spyOn(notificationApi, "list").mockResolvedValue({
    items: [],
    total: 0,
    unread_count: 0,
  });
});

Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});

window.getComputedStyle = ((_element: Element) => ({
  getPropertyValue: (property: string) => {
    if (property === "width") return "0px";
    if (property === "height") return "0px";
    if (property === "overflow") return "auto";
    return "";
  },
})) as typeof window.getComputedStyle;

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

global.ResizeObserver = ResizeObserverMock as typeof ResizeObserver;

Element.prototype.scrollIntoView = () => {};
