import { afterEach } from 'vitest';
import '@testing-library/jest-dom/vitest';

afterEach(() => {
    // Limpia el DOM entre tests para evitar fugas entre renderizados
    document.body.innerHTML = '';
});
