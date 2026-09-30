import type { MembershipSelectProps } from '../../types/MemberFormTypes';
import { formatCurrencyCOP } from '../../utils/formatters';
import Select from '../ui/Select';
import Label from '../ui/Label';

const MembershipSelect = (
  { register, errors, membresias, onChange, disabled = false, readOnly = false, value }: MembershipSelectProps
) => {
    const errorMessage = errors.membresia?.message;
    const errorId = errorMessage ? 'membresia-error' : undefined;
    const registerResult = register('membresia');

    const handleChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
      registerResult.onChange(event);
      onChange(event);
    };

    const currentValue = value ?? '';

    return (
      <div className="relative pt-5">
        {/* Hidden input ensures value submits even when select is disabled (readOnly mode) */}
        {readOnly && currentValue && (
          <input type="hidden" name="membresia" value={currentValue} />
        )}
        <Select
          ref={registerResult.ref}
          id="membresia"
          name={registerResult.name}
          onBlur={registerResult.onBlur}
          onChange={readOnly ? undefined : handleChange}
          disabled={disabled || readOnly}
          value={currentValue}
          aria-invalid={!!errorMessage}
          aria-describedby={errorId}
          aria-label="Seleccionar membresía"
          aria-readonly={readOnly}
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
};

MembershipSelect.displayName = 'MembershipSelect';

export { MembershipSelect };