import { forwardRef } from 'react';
import type { ExistingMemberSelectProps } from '../../types/MemberFormTypes';
import Select from '../ui/Select';
import Label from '../ui/Label';

const ExistingMemberSelect = forwardRef<HTMLSelectElement, ExistingMemberSelectProps>(
  ({ register, errors, miembros, disabled = false, ...props }, ref) => {
    const errorMessage = errors.miembro?.message;
    const errorId = errorMessage ? 'miembro-error' : undefined;
    const registerResult = register('miembro');
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { ref: _registerRef, ...registerProps } = registerResult;

    return (
      <div className="relative pt-5">
        <Select
          ref={ref}
          id="miembro"
          {...registerProps}
          disabled={disabled}
          aria-invalid={!!errorMessage}
          aria-describedby={errorId}
          aria-label="Seleccionar miembro"
          {...props}
        >
          <option value="">Seleccionar miembro...</option>
          {miembros.map((miembro) => (
            <option key={miembro.id} value={miembro.id.toString()}>
              {miembro.name} {miembro.lastname} - {miembro.phone}
            </option>
          ))}
        </Select>
        <Label htmlFor="miembro">Miembro</Label>
        {errorMessage && (
          <span id={errorId} className="text-red-500 text-sm" role="alert">
            {errorMessage}
          </span>
        )}
      </div>
    );
  }
);

ExistingMemberSelect.displayName = 'ExistingMemberSelect';

export { ExistingMemberSelect };