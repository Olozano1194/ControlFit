import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ModeToggle } from '../../../components/memberForm/ModeToggle';

describe('ModeToggle', () => {
  const mockOnChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders both mode options with correct labels', () => {
    render(<ModeToggle modo="existente" onChange={mockOnChange} />);

    expect(screen.getByText('Miembro existente')).toBeInTheDocument();
    expect(screen.getByText('Nuevo miembro')).toBeInTheDocument();
  });

  it('shows "Miembro existente" as active when modo is "existente"', () => {
    render(<ModeToggle modo="existente" onChange={mockOnChange} />);

    const existenteButton = screen.getByText('Miembro existente').closest('button');
    const nuevoButton = screen.getByText('Nuevo miembro').closest('button');

    expect(existenteButton).toHaveAttribute('aria-pressed', 'true');
    expect(nuevoButton).toHaveAttribute('aria-pressed', 'false');
  });

  it('shows "Nuevo miembro" as active when modo is "nuevo"', () => {
    render(<ModeToggle modo="nuevo" onChange={mockOnChange} />);

    const existenteButton = screen.getByText('Miembro existente').closest('button');
    const nuevoButton = screen.getByText('Nuevo miembro').closest('button');

    expect(existenteButton).toHaveAttribute('aria-pressed', 'false');
    expect(nuevoButton).toHaveAttribute('aria-pressed', 'true');
  });

  it('calls onChange when clicking "Miembro existente"', () => {
    render(<ModeToggle modo="nuevo" onChange={mockOnChange} />);

    fireEvent.click(screen.getByText('Miembro existente'));

    expect(mockOnChange).toHaveBeenCalledTimes(1);
    expect(mockOnChange).toHaveBeenCalledWith('existente');
  });

  it('calls onChange when clicking "Nuevo miembro"', () => {
    render(<ModeToggle modo="existente" onChange={mockOnChange} />);

    fireEvent.click(screen.getByText('Nuevo miembro'));

    expect(mockOnChange).toHaveBeenCalledTimes(1);
    expect(mockOnChange).toHaveBeenCalledWith('nuevo');
  });

  it('does not call onChange when clicking already active mode', () => {
    render(<ModeToggle modo="existente" onChange={mockOnChange} />);

    fireEvent.click(screen.getByText('Miembro existente'));

    expect(mockOnChange).not.toHaveBeenCalled();
  });

  it('disables both buttons when disabled prop is true', () => {
    render(<ModeToggle modo="existente" onChange={mockOnChange} disabled={true} />);

    const existenteButton = screen.getByText('Miembro existente').closest('button');
    const nuevoButton = screen.getByText('Nuevo miembro').closest('button');

    expect(existenteButton).toBeDisabled();
    expect(nuevoButton).toBeDisabled();
  });

  it('does not call onChange when disabled', () => {
    render(<ModeToggle modo="existente" onChange={mockOnChange} disabled={true} />);

    fireEvent.click(screen.getByText('Nuevo miembro'));

    expect(mockOnChange).not.toHaveBeenCalled();
  });

  it('renders with proper role and accessibility attributes', () => {
    render(<ModeToggle modo="existente" onChange={mockOnChange} />);

    const container = screen.getByRole('radiogroup');
    expect(container).toBeInTheDocument();
  });
});