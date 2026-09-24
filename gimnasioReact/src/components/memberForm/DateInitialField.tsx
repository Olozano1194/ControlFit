import type { DateInitialFieldProps } from '../../types/MemberFormTypes';
import Input from '../ui/Input';
import Label from '../ui/Label';

export function DateInitialField({ register, errors, disabled = false }: DateInitialFieldProps) {
  const errorMessage = errors.dateInitial?.message;
  const errorId = errorMessage ? 'dateInitial-error' : undefined;
  const registerResult = register('dateInitial');

  return (
    <div className="relative pt-5">
      <Input
        id="dateInitial"
        type="date"
        required
        disabled={disabled}
        aria-invalid={!!errorMessage}
        aria-describedby={errorId}
        {...registerResult}
      />
      <Label htmlFor="dateInitial">Fecha Inicial</Label>
      {errorMessage && (
        <span id={errorId} className="text-red-500 text-sm" role="alert">
          {errorMessage}
        </span>
      )}
    </div>
  );
}