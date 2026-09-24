import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MultiplierDiscountFields } from '../../../components/memberForm/MultiplierDiscountFields';

const mockProps = {
  multiplier: 3,
  discountPercent: 5,
  multiplierOptions: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
  onMultiplierChange: vi.fn(),
  onDiscountChange: vi.fn(),
  disabled: false,
};

describe('MultiplierDiscountFields', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders multiplier select with all options', () => {
    render(<MultiplierDiscountFields {...mockProps} />);

    const select = screen.getByLabelText('Periodos');
    expect(select).toBeInTheDocument();

    const options = select.querySelectorAll('option');
    expect(options).toHaveLength(12);
    expect(options[0]).toHaveValue('1');
    expect(options[0]).toHaveTextContent('1 mes');
    expect(options[1]).toHaveValue('2');
    expect(options[1]).toHaveTextContent('2 meses');
    expect(options[11]).toHaveValue('12');
    expect(options[11]).toHaveTextContent('12 meses');
  });

  it('shows current multiplier as selected', () => {
    render(<MultiplierDiscountFields {...mockProps} />);

    const select = screen.getByLabelText('Periodos');
    expect(select).toHaveValue('3');
  });

  it('calls onMultiplierChange when multiplier changes', () => {
    render(<MultiplierDiscountFields {...mockProps} />);

    const select = screen.getByLabelText('Periodos');
    fireEvent.change(select, { target: { value: '6' } });

    expect(mockProps.onMultiplierChange).toHaveBeenCalled();
  });

  it('renders discount input with correct value', () => {
    render(<MultiplierDiscountFields {...mockProps} />);

    const input = screen.getByLabelText('Descuento (%)');
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute('type', 'number');
    expect(input).toHaveAttribute('min', '0');
    expect(input).toHaveAttribute('max', '100');
    expect(input).toHaveAttribute('step', '0.5');
    // Value can be string or number depending on jsdom
    expect(input).toHaveValue(5);
  });

  it('calls onDiscountChange with number value when discount changes', () => {
    render(<MultiplierDiscountFields {...mockProps} />);

    const input = screen.getByLabelText('Descuento (%)');
    fireEvent.change(input, { target: { value: '10' } });

    expect(mockProps.onDiscountChange).toHaveBeenCalledWith(10);
  });

  it('applies disabled state to both fields when disabled prop is true', () => {
    render(<MultiplierDiscountFields {...mockProps} disabled={true} />);

    const select = screen.getByLabelText('Periodos');
    const input = screen.getByLabelText('Descuento (%)');
    expect(select).toBeDisabled();
    expect(input).toBeDisabled();
  });

  it('does not call callbacks when disabled', () => {
    render(<MultiplierDiscountFields {...mockProps} disabled={true} />);

    const select = screen.getByLabelText('Periodos');
    const input = screen.getByLabelText('Descuento (%)');
    fireEvent.change(select, { target: { value: '6' } });
    fireEvent.change(input, { target: { value: '10' } });

    expect(mockProps.onMultiplierChange).not.toHaveBeenCalled();
    expect(mockProps.onDiscountChange).not.toHaveBeenCalled();
  });

  it('handles empty multiplier options', () => {
    render(<MultiplierDiscountFields {...mockProps} multiplierOptions={[]} />);

    const select = screen.getByLabelText('Periodos');
    const options = select.querySelectorAll('option');
    expect(options).toHaveLength(0);
  });

  it('associates labels with inputs via htmlFor', () => {
    render(<MultiplierDiscountFields {...mockProps} />);

    const select = screen.getByLabelText('Periodos');
    const input = screen.getByLabelText('Descuento (%)');
    expect(select).toHaveAttribute('id', 'multiplier');
    expect(input).toHaveAttribute('id', 'discountPercent');
  });
});