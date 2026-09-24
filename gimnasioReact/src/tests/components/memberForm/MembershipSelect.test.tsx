import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MembershipSelect } from '../../../components/memberForm/MembershipSelect';
import type { SelectedMembresia, FormRegister, FormErrors } from '../../../types/MemberFormTypes';

const mockMembresias: SelectedMembresia[] = [
  { id: 1, name: 'Básica', price: 50000, duration: 30, max_multiplier: 12, gimnasio: 1 },
  { id: 2, name: 'Premium', price: 100000, duration: 30, max_multiplier: 12, gimnasio: 1 },
  { id: 3, name: 'VIP', price: 200000, duration: 30, max_multiplier: 6, gimnasio: 1 },
];

const createMockRegister = (onChange?: (e: React.ChangeEvent<HTMLSelectElement>) => void): FormRegister => {
  const registerObj = {
    ref: vi.fn(),
    onChange: onChange ?? vi.fn(),
    onBlur: vi.fn(),
  };
  return vi.fn(() => registerObj) as unknown as FormRegister;
};

const mockErrors: FormErrors = {};
const mockOnChange = vi.fn();

describe('MembershipSelect', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders select with placeholder option', () => {
    const register = createMockRegister();
    render(<MembershipSelect register={register} errors={mockErrors} membresias={mockMembresias} onChange={mockOnChange} />);

    expect(screen.getByRole('combobox')).toBeInTheDocument();
    expect(screen.getByText('Seleccionar membresía...')).toBeInTheDocument();
  });

  it('renders all memberships as options with name and formatted price', () => {
    const register = createMockRegister();
    render(<MembershipSelect register={register} errors={mockErrors} membresias={mockMembresias} onChange={mockOnChange} />);

    const select = screen.getByRole('combobox');
    const options = select.querySelectorAll('option');

    expect(options).toHaveLength(4); // placeholder + 3 memberships
    expect(options[1]).toHaveValue('1');
    expect(options[1]).toHaveTextContent('Básica - $ 50.000');
    expect(options[2]).toHaveValue('2');
    expect(options[2]).toHaveTextContent('Premium - $ 100.000');
    expect(options[3]).toHaveValue('3');
    expect(options[3]).toHaveTextContent('VIP - $ 200.000');
  });

  it('calls register onChange and onChange prop when selection changes', () => {
    const registerOnChange = vi.fn();
    const register = createMockRegister(registerOnChange);
    render(<MembershipSelect register={register} errors={mockErrors} membresias={mockMembresias} onChange={mockOnChange} />);

    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: '2' } });

    expect(registerOnChange).toHaveBeenCalled();
    expect(mockOnChange).toHaveBeenCalled();
  });

  it('displays error message when errors.membresia exists', () => {
    const register = createMockRegister();
    const errorsWithMessage: FormErrors = {
      membresia: { message: 'Membresía requerida', type: 'required' },
    };

    render(<MembershipSelect register={register} errors={errorsWithMessage} membresias={mockMembresias} onChange={mockOnChange} />);

    expect(screen.getByText('Membresía requerida')).toBeInTheDocument();
  });

  it('applies disabled state when disabled prop is true', () => {
    const register = createMockRegister();
    render(<MembershipSelect register={register} errors={mockErrors} membresias={mockMembresias} onChange={mockOnChange} disabled={true} />);

    const select = screen.getByRole('combobox');
    expect(select).toBeDisabled();
  });

  it('applies error styling when error exists', () => {
    const register = createMockRegister();
    const errorsWithMessage: FormErrors = {
      membresia: { message: 'Membresía requerida', type: 'required' },
    };

    render(<MembershipSelect register={register} errors={errorsWithMessage} membresias={mockMembresias} onChange={mockOnChange} />);

    const select = screen.getByRole('combobox');
    expect(select).toHaveAttribute('aria-invalid', 'true');
    expect(select).toHaveAttribute('aria-describedby');
  });

  it('associates label with select via htmlFor', () => {
    const register = createMockRegister();
    render(<MembershipSelect register={register} errors={mockErrors} membresias={mockMembresias} onChange={mockOnChange} />);

    const label = screen.getByLabelText('Membresía');
    expect(label).toBeInTheDocument();
  });

  it('renders only active memberships (filters by is_active)', () => {
    const membresiasWithInactive: SelectedMembresia[] = [
      ...mockMembresias,
      { id: 4, name: 'Inactiva', price: 10000, duration: 30, max_multiplier: 12, is_active: false, gimnasio: 1 },
    ];
    const register = createMockRegister();
    render(<MembershipSelect register={register} errors={mockErrors} membresias={membresiasWithInactive} onChange={mockOnChange} />);

    const select = screen.getByRole('combobox');
    const options = select.querySelectorAll('option');
    // Should only show active memberships (3) + placeholder = 4
    expect(options).toHaveLength(4);
  });
});