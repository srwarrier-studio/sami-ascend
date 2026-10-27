import '@testing-library/jest-dom/vitest'

window.matchMedia = (query: string) =>
  ({
    matches: false,
    media: query,
    addEventListener: () => {},
    removeEventListener: () => {},
    addListener: () => {},
    removeListener: () => {},
    onchange: null,
    dispatchEvent: () => false,
  }) as MediaQueryList

globalThis.ResizeObserver = class {
  observe() {}
  unobserve() {}
  disconnect() {}
}
