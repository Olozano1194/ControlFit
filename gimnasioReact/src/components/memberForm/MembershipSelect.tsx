import { forwardRef } from 'react';
import type { MembershipSelectProps } from '../../types/MemberFormTypes';
import { formatCurrencyCOP } from '../../utils/formatters';
import Select from '../ui/Select';
import Label from '../ui/Label';

const MembershipSelect = forwardRef<HTMLSelectElement, MembershipSelectProps>(
  ({ register, errors, membresias, onChange, disabled = false, ...props }, ref) => {
    const errorMessage = errors.membresia?.message;
    const errorId = errorMessage ? 'membresia-error' : undefined;
    const registerResult = register('membresia');
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { ref: _registerRef, ...registerProps } = registerResult;

    const handleChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
      registerProps.onChange(event);
      onChange(event);
    };

    return (
      <div className="relative pt-5">
        <Select
          ref={ref}
          id="membresia"
          {...registerProps}
          onChange={handleChange}
          disabled={disabled}
          aria-invalid={!!errorMessage}
          aria-describedby={errorId}
          aria-label="Seleccionar membresía"
          {...props}
        >
          <option value="">Seleccionar membresía...</option>
          {membresias
            .filter((m) => m.is_active !== false)
            .map((membresia) => (
              <option key={membresia.id} value={membresia.id.toString()}>
                {membresia.name} - {formatCurrencyCOP(membresia.price)}
              </option>
            ))}
        </Select>
        <Label htmlFor="membresia">Membresía</Label>
        {errorMessage && (
          <span id={errorId} className="text-red-500 text-sm" role="alert">
            {errorMessage}
          </span>
        )}
      </div>
    );
  }
);

MembershipSelect.displayName = 'MembershipSelect';

export { MembershipSelect };