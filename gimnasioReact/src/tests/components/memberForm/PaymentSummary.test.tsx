import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PaymentSummary } from '../../../components/memberForm/PaymentSummary';
import type { SelectedMembresia } from '../../../types/MemberFormTypes';

const mockMembresia: SelectedMembresia = {
  id: 1,
  name: 'Premium',
  price: 100000,
  duration: 30,
  max_multiplier: 12,
  gimnasio: 1,
};

const mockProps = {
  selectedMembresia: mockMembresia,
  multiplier: 3,
  discountPercent: 10,
  estimatedPrice: 270000,
  totalDays: 90,
  estimatedDateFinal: '15/04/2024',
  disabled: false,
};

describe('PaymentSummary', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders summary card with all fields', () => {
    render(<PaymentSummary {...mockProps} />);

    expect(screen.getByText('Resumen del pago')).toBeInTheDocument();
    expect(screen.getByText('Premium')).toBeInTheDocument();
    expect(screen.getByText('$ 100.000')).toBeInTheDocument();
    expect(screen.getByText('15/04/2024')).toBeInTheDocument();
    expect(screen.getByText('90 días')).toBeInTheDocument();
    expect(screen.getByText('3x')).toBeInTheDocument();
    expect(screen.getByText(/10%/)).toBeInTheDocument();
    expect(screen.getByText('$ 270.000')).toBeInTheDocument();
  });

  it('shows membership name and price', () => {
    render(<PaymentSummary {...mockProps} />);

    expect(screen.getByText('Membresía:')).toBeInTheDocument();
    expect(screen.getByText('Premium')).toBeInTheDocument();
    expect(screen.getByText('Valor unitario:')).toBeInTheDocument();
    expect(screen.getByText('$ 100.000')).toBeInTheDocument();
  });

  it('shows initial and final dates', () => {
    render(<PaymentSummary {...mockProps} />);

    expect(screen.getByText('Fecha inicio:')).toBeInTheDocument();
    expect(screen.getByText('Fecha fin:')).toBeInTheDocument();
  });

  it('shows total days, multiplier, and discount', () => {
    render(<PaymentSummary {...mockProps} />);

    expect(screen.getByText('Días totales:')).toBeInTheDocument();
    expect(screen.getByText('90 días')).toBeInTheDocument();
    expect(screen.getByText('Multiplicador:')).toBeInTheDocument();
    expect(screen.getByText('3x')).toBeInTheDocument();
    expect(screen.getByText(/Descuento/)).toBeInTheDocument();
    expect(screen.getByText(/10%/)).toBeInTheDocument();
  });

  it('shows final price prominently', () => {
    render(<PaymentSummary {...mockProps} />);

    expect(screen.getByText('Total a pagar:')).toBeInTheDocument();
    expect(screen.getByText('$ 270.000')).toBeInTheDocument();
  });

  it('handles null membership gracefully', () => {
    render(<PaymentSummary {...mockProps} selectedMembresia={null} />);

    expect(screen.queryByText('Resumen del pago')).not.toBeInTheDocument();
  });

  it('handles zero price membership', () => {
    const freeMembresia: SelectedMembresia = { ...mockMembresia, price: 0 };
    render(<PaymentSummary {...mockProps} selectedMembresia={freeMembresia} estimatedPrice={0} />);

    // With price <= 0, component returns null
    expect(screen.queryByText('Resumen del pago')).not.toBeInTheDocument();
  });

  it('applies dimmed style when disabled', () => {
    render(<PaymentSummary {...mockProps} disabled={true} />);

    const container = screen.getByText('Resumen del pago').closest('div');
    expect(container).toHaveClass('opacity-50');
  });

  it('formats currency using COP format', () => {
    render(<PaymentSummary {...mockProps} estimatedPrice={1234567} />);

    expect(screen.getByText('$ 1.234.567')).toBeInTheDocument();
  });

  it('formats dates in DD/MM/YYYY format', () => {
    render(<PaymentSummary {...mockProps} estimatedDateFinal='31/12/2024' />);

    expect(screen.getByText('31/12/2024')).toBeInTheDocument();
  });
});