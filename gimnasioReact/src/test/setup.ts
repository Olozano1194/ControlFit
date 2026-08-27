import { afterEach, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

// Polyfill for matchMedia (used by react-hot-toast)
Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation(query => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
    })),
});

afterEach(() => {
    // Limpia el DOM entre tests para evitar fugas entre renderizados
    document.body.innerHTML = '';
});
