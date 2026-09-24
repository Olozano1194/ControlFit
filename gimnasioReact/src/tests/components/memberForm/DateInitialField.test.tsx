import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DateInitialField } from '../../../components/memberForm/DateInitialField';
import type { FormRegister, FormErrors } from '../../../types/MemberFormTypes';

const createMockRegister = (values: Record<string, string> = {}): FormRegister => {
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

describe('DateInitialField', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders date input with correct type', () => {
    const register = createMockRegister();
    render(<DateInitialField register={register} errors={mockErrors} />);

    const input = screen.getByLabelText('Fecha Inicial');
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute('type', 'date');
  });

  it('registers dateInitial field with required validation', () => {
    const values: Record<string, string> = {};
    const register = createMockRegister(values);
    render(<DateInitialField register={register} errors={mockErrors} />);

    const input = screen.getByLabelText('Fecha Inicial') as HTMLInputElement;
    fireEvent.change(input, { target: { value: '2024-01-15' } });

    expect(values.dateInitial).toBe('2024-01-15');
  });

  it('displays error message when errors.dateInitial exists', () => {
    const register = createMockRegister();
    const errorsWithMessage: FormErrors = {
      dateInitial: { message: 'Fecha requerida', type: 'required' },
    };

    render(<DateInitialField register={register} errors={errorsWithMessage} />);

    expect(screen.getByText('Fecha requerida')).toBeInTheDocument();
  });

  it('applies disabled state when disabled prop is true', () => {
    const register = createMockRegister();
    render(<DateInitialField register={register} errors={mockErrors} disabled={true} />);

    const input = screen.getByLabelText('Fecha Inicial');
    expect(input).toBeDisabled();
  });

  it('applies error styling when error exists', () => {
    const register = createMockRegister();
    const errorsWithMessage: FormErrors = {
      dateInitial: { message: 'Fecha requerida', type: 'required' },
    };

    render(<DateInitialField register={register} errors={errorsWithMessage} />);

    const input = screen.getByLabelText('Fecha Inicial');
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(input).toHaveAttribute('aria-describedby');
  });

  it('associates label with input via htmlFor', () => {
    const register = createMockRegister();
    render(<DateInitialField register={register} errors={mockErrors} />);

    const label = screen.getByLabelText('Fecha Inicial');
    expect(label).toBeInTheDocument();
  });

  it('has correct id attribute', () => {
    const register = createMockRegister();
    render(<DateInitialField register={register} errors={mockErrors} />);

    const input = screen.getByLabelText('Fecha Inicial');
    expect(input).toHaveAttribute('id', 'dateInitial');
  });

  it('applies required attribute', () => {
    const register = createMockRegister();
    render(<DateInitialField register={register} errors={mockErrors} />);

    const input = screen.getByLabelText('Fecha Inicial');
    expect(input).toBeRequired();
  });
});