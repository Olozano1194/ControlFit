import type { NewMemberFieldsProps } from '../../types/MemberFormTypes';
import Input from '../ui/Input';
import Label from '../ui/Label';

export function NewMemberFields({ register, errors, disabled = false }: NewMemberFieldsProps) {
  const nameError = errors.nuevoName?.message;
  const lastnameError = errors.nuevoLastname?.message;
  const phoneError = errors.nuevoPhone?.message;
  const addressError = errors.nuevoAddress?.message;

  return (
    <section className="gap-y-10 gap-x-8 grid grid-cols-1 md:grid-cols-2">
      <div className="relative pt-5">
        <Input
          id="nuevoName"
          type="text"
          required
          disabled={disabled}
          aria-invalid={!!nameError}
          aria-describedby={nameError ? 'nuevoName-error' : undefined}
          {...register('nuevoName', {
            required: { value: true, message: 'Nombre requerido' },
            minLength: { value: 4, message: 'El nombre debe tener como mínimo 4 letras' },
            maxLength: { value: 20, message: 'El nombre debe tener como máximo 20 letras' },
            pattern: { value: /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/, message: 'Nombre inválido' },
          })}
        />
        <Label htmlFor="nuevoName">Nombres *</Label>
        {nameError && (
          <span id="nuevoName-error" className="text-red-500 text-sm" role="alert">
            {nameError}
          </span>
        )}
      </div>
      <div className="relative pt-5">
        <Input
          id="nuevoLastname"
          type="text"
          required
          disabled={disabled}
          aria-invalid={!!lastnameError}
          aria-describedby={lastnameError ? 'nuevoLastname-error' : undefined}
          {...register('nuevoLastname', {
            required: { value: true, message: 'Apellido requerido' },
            minLength: { value: 5, message: 'El apellido debe tener como mínimo 5 letras' },
            maxLength: { value: 20, message: 'El apellido debe tener como máximo 20 letras' },
            pattern: { value: /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/, message: 'Apellido inválido' },
          })}
        />
        <Label htmlFor="nuevoLastname">Apellidos *</Label>
        {lastnameError && (
          <span id="nuevoLastname-error" className="text-red-500 text-sm" role="alert">
            {lastnameError}
          </span>
        )}
      </div>
      <div className="relative pt-5">
        <Input
          id="nuevoPhone"
          type="tel"
          required
          disabled={disabled}
          aria-invalid={!!phoneError}
          aria-describedby={phoneError ? 'nuevoPhone-error' : undefined}
          {...register('nuevoPhone', {
            required: { value: true, message: 'Celular requerido' },
            minLength: { value: 10, message: 'El celular debe tener como mínimo 10 números' },
            maxLength: { value: 10, message: 'El celular debe tener como máximo 10 números' },
            pattern: { value: /^[0-9]+$/, message: 'Número celular inválido' },
          })}
        />
        <Label htmlFor="nuevoPhone">Celular *</Label>
        {phoneError && (
          <span id="nuevoPhone-error" className="text-red-500 text-sm" role="alert">
            {phoneError}
          </span>
        )}
      </div>
      <div className="relative pt-5">
        <Input
          id="nuevoAddress"
          type="text"
          maxLength={50}
          disabled={disabled}
          aria-invalid={!!addressError}
          aria-describedby={addressError ? 'nuevoAddress-error' : undefined}
          {...register('nuevoAddress', {
            maxLength: { value: 50, message: 'La dirección debe tener como máximo 50 caracteres' },
          })}
        />
        <Label htmlFor="nuevoAddress">Dirección</Label>
        {addressError && (
          <span id="nuevoAddress-error" className="text-red-500 text-sm" role="alert">
            {addressError}
          </span>
        )}
      </div>
    </section>
  );
}