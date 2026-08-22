import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';

describe('Vitest setup', () => {
    it('renderiza componentes React en jsdom', () => {
        render(<p>ControlFit Platform</p>);
        expect(screen.getByText('ControlFit Platform')).toBeInTheDocument();
    });
});
