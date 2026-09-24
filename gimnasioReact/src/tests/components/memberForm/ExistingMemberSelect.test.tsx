import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ExistingMemberSelect } from '../../../components/memberForm/ExistingMemberSelect';
import type { Miembro, FormRegister, FormErrors } from '../../../types/MemberFormTypes';

const mockMiembros: Miembro[] = [
  { id: 1, name: 'Juan', lastname: 'Pérez', phone: '3001234567', address: 'Calle 123' },
  { id: 2, name: 'María', lastname: 'García', phone: '3009876543', address: 'Carrera 456' },
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

describe('ExistingMemberSelect', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders select with placeholder option', () => {
    const register = createMockRegister();
    render(<ExistingMemberSelect register={register} errors={mockErrors} miembros={mockMiembros} />);

    expect(screen.getByRole('combobox')).toBeInTheDocument();
    expect(screen.getByText('Seleccionar miembro...')).toBeInTheDocument();
  });

  it('renders all members as options with correct format', () => {
    const register = createMockRegister();
    render(<ExistingMemberSelect register={register} errors={mockErrors} miembros={mockMiembros} />);

    const select = screen.getByRole('combobox');
    const options = select.querySelectorAll('option');

    expect(options).toHaveLength(3); // placeholder + 2 members
    expect(options[1]).toHaveValue('1');
    expect(options[1]).toHaveTextContent('Juan Pérez - 3001234567');
    expect(options[2]).toHaveValue('2');
    expect(options[2]).toHaveTextContent('María García - 3009876543');
  });

  it('calls register onChange when selection changes', () => {
    const onChange = vi.fn();
    const register = createMockRegister(onChange);
    render(<ExistingMemberSelect register={register} errors={mockErrors} miembros={mockMiembros} />);

    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: '1' } });

    expect(onChange).toHaveBeenCalled();
  });

  it('displays error message when errors.miembro exists', () => {
    const register = createMockRegister();
    const errorsWithMessage: FormErrors = {
      miembro: { message: 'Nombre requerido', type: 'required' },
    };

    render(<ExistingMemberSelect register={register} errors={errorsWithMessage} miembros={mockMiembros} />);

    expect(screen.getByText('Nombre requerido')).toBeInTheDocument();
  });

  it('applies disabled state when disabled prop is true', () => {
    const register = createMockRegister();
    render(<ExistingMemberSelect register={register} errors={mockErrors} miembros={mockMiembros} disabled={true} />);

    const select = screen.getByRole('combobox');
    expect(select).toBeDisabled();
  });

  it('applies error styling when error exists', () => {
    const register = createMockRegister();
    const errorsWithMessage: FormErrors = {
      miembro: { message: 'Nombre requerido', type: 'required' },
    };

    render(<ExistingMemberSelect register={register} errors={errorsWithMessage} miembros={mockMiembros} />);

    const select = screen.getByRole('combobox');
    expect(select).toHaveAttribute('aria-invalid', 'true');
    expect(select).toHaveAttribute('aria-describedby');
  });

  it('renders empty state when no members provided', () => {
    const register = createMockRegister();
    render(<ExistingMemberSelect register={register} errors={mockErrors} miembros={[]} />);

    const select = screen.getByRole('combobox');
    const options = select.querySelectorAll('option');
    expect(options).toHaveLength(1); // only placeholder
    expect(screen.getByText('Seleccionar miembro...')).toBeInTheDocument();
  });

  it('associates label with select via htmlFor', () => {
    const register = createMockRegister();
    render(<ExistingMemberSelect register={register} errors={mockErrors} miembros={mockMiembros} />);

    const label = screen.getByLabelText('Miembro');
    expect(label).toBeInTheDocument();
  });
});