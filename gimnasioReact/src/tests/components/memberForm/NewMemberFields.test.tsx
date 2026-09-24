import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { NewMemberFields } from '../../../components/memberForm/NewMemberFields';
import type { FormRegister, FormErrors } from '../../../types/MemberFormTypes';

const createMockRegister = (values: Record<string, string> = {}) => {
  const registerObj = (fieldName: string) => ({
    ref: vi.fn(),
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => {
      values[fieldName] = e.target.value;
    },
    onBlur: vi.fn(),
    name: fieldName,
  });
  return vi.fn(registerObj) as unknown as FormRegister;
};

const mockErrors: FormErrors = {};

describe('NewMemberFields', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all four input fields', () => {
    const register = createMockRegister();
    render(<NewMemberFields register={register} errors={mockErrors} />);

    expect(screen.getByLabelText('Nombres *')).toBeInTheDocument();
    expect(screen.getByLabelText('Apellidos *')).toBeInTheDocument();
    expect(screen.getByLabelText('Celular *')).toBeInTheDocument();
    expect(screen.getByLabelText('Dirección')).toBeInTheDocument();
  });

  it('registers all fields with correct validation rules', () => {
    const values: Record<string, string> = {};
    const register = createMockRegister(values);
    render(<NewMemberFields register={register} errors={mockErrors} />);

    const nombreInput = screen.getByLabelText('Nombres *') as HTMLInputElement;
    const apellidoInput = screen.getByLabelText('Apellidos *') as HTMLInputElement;
    const celularInput = screen.getByLabelText('Celular *') as HTMLInputElement;
    const direccionInput = screen.getByLabelText('Dirección') as HTMLInputElement;

    fireEvent.change(nombreInput, { target: { value: 'Juan' } });
    fireEvent.change(apellidoInput, { target: { value: 'Pérez' } });
    fireEvent.change(celularInput, { target: { value: '3001234567' } });
    fireEvent.change(direccionInput, { target: { value: 'Calle 123' } });

    expect(values.nuevoName).toBe('Juan');
    expect(values.nuevoLastname).toBe('Pérez');
    expect(values.nuevoPhone).toBe('3001234567');
    expect(values.nuevoAddress).toBe('Calle 123');
  });

  it('displays error messages when errors exist', () => {
    const register = createMockRegister();
    const errorsWithMessages: FormErrors = {
      nuevoName: { message: 'El nombre debe tener como mínimo 4 letras', type: 'minLength' },
      nuevoLastname: { message: 'El apellido debe tener como mínimo 5 letras', type: 'minLength' },
      nuevoPhone: { message: 'Número celular inválido', type: 'pattern' },
      nuevoAddress: { message: 'La dirección debe tener como máximo 50 caracteres', type: 'maxLength' },
    };

    render(<NewMemberFields register={register} errors={errorsWithMessages} />);

    expect(screen.getByText('El nombre debe tener como mínimo 4 letras')).toBeInTheDocument();
    expect(screen.getByText('El apellido debe tener como mínimo 5 letras')).toBeInTheDocument();
    expect(screen.getByText('Número celular inválido')).toBeInTheDocument();
    expect(screen.getByText('La dirección debe tener como máximo 50 caracteres')).toBeInTheDocument();
  });

  it('applies disabled state to all inputs when disabled prop is true', () => {
    const register = createMockRegister();
    render(<NewMemberFields register={register} errors={mockErrors} disabled={true} />);

    const inputs = screen.getAllByRole('textbox');
    inputs.forEach((input) => {
      expect(input).toBeDisabled();
    });
  });

  it('applies required attribute to required fields', () => {
    const register = createMockRegister();
    render(<NewMemberFields register={register} errors={mockErrors} />);

    const nombreInput = screen.getByLabelText('Nombres *');
    const apellidoInput = screen.getByLabelText('Apellidos *');
    const celularInput = screen.getByLabelText('Celular *');

    expect(nombreInput).toBeRequired();
    expect(apellidoInput).toBeRequired();
    expect(celularInput).toBeRequired();
  });

  it('does not apply required attribute to optional address field', () => {
    const register = createMockRegister();
    render(<NewMemberFields register={register} errors={mockErrors} />);

    const direccionInput = screen.getByLabelText('Dirección');
    expect(direccionInput).not.toBeRequired();
  });

  it('uses correct input types', () => {
    const register = createMockRegister();
    render(<NewMemberFields register={register} errors={mockErrors} />);

    const nombreInput = screen.getByLabelText('Nombres *') as HTMLInputElement;
    const apellidoInput = screen.getByLabelText('Apellidos *') as HTMLInputElement;
    const celularInput = screen.getByLabelText('Celular *') as HTMLInputElement;
    const direccionInput = screen.getByLabelText('Dirección') as HTMLInputElement;

    expect(nombreInput).toHaveAttribute('type', 'text');
    expect(apellidoInput).toHaveAttribute('type', 'text');
    expect(celularInput).toHaveAttribute('type', 'tel');
    expect(direccionInput).toHaveAttribute('type', 'text');
  });

  it('applies maxLength to address field', () => {
    const register = createMockRegister();
    render(<NewMemberFields register={register} errors={mockErrors} />);

    const direccionInput = screen.getByLabelText('Dirección') as HTMLInputElement;
    expect(direccionInput).toHaveAttribute('maxLength', '50');
  });

  it('associates each label with its input via htmlFor', () => {
    const register = createMockRegister();
    render(<NewMemberFields register={register} errors={mockErrors} />);

    const nombreInput = screen.getByLabelText('Nombres *');
    const apellidoInput = screen.getByLabelText('Apellidos *');
    const celularInput = screen.getByLabelText('Celular *');
    const direccionInput = screen.getByLabelText('Dirección');

    expect(nombreInput).toHaveAttribute('id', 'nuevoName');
    expect(apellidoInput).toHaveAttribute('id', 'nuevoLastname');
    expect(celularInput).toHaveAttribute('id', 'nuevoPhone');
    expect(direccionInput).toHaveAttribute('id', 'nuevoAddress');
  });
});