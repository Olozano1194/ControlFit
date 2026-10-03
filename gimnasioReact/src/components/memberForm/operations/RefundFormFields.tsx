import { Controller, type Control, type FieldErrors } from 'react-hook-form';
import Input from '@/components/ui/Input';
import Label from '@/components/ui/Label';
import type { RefundFormData } from './useRefundModal';

interface RefundFormFieldsProps {
  control: Control<RefundFormData>;
  errors: FieldErrors<RefundFormData>;
}

export function RefundFormFields({
  control,
  errors,
}: RefundFormFieldsProps) {
  return (
    <>
      <div>
        <Label htmlFor="monto">Monto a devolver <span className="text-red-500">*</span></Label>
        <Controller
          name="monto"
          control={control}
          render={({ field }) => (
            <Input
              id="monto"
              type="number"
              step="0.01"
              min="0.01"
              {...field}
              value={field.value}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                field.onChange(e.target.value);
              }}
              className={`mt-1 w-full ${errors.monto ? 'border-red-500 focus:ring-red-500 focus:border-red-500' : 'border-gray-300 focus:ring-sky-500 focus:border-sky-500'}`}
              placeholder="Ej: 10000.00"
            />
          )}
        />
        {errors.monto && (
          <span className="text-red-500 text-sm" role="alert">{errors.monto.message}</span>
        )}
      </div>

      <div>
        <Label htmlFor="reason">Motivo <span className="text-red-500">*</span></Label>
        <Controller
          name="reason"
          control={control}
          rules={{
            required: { value: true, message: 'El motivo es obligatorio' },
            minLength: { value: 10, message: 'El motivo debe tener al menos 10 caracteres' },
          }}
          render={({ field }) => (
            <textarea
              id="reason"
              rows={3}
              {...field}
              value={field.value}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => {
                field.onChange(e.target.value);
              }}
              className={`mt-1 w-full rounded-lg border p-3 text-base ${
                errors.reason
                  ? 'border-red-500 focus:ring-red-500 focus:border-red-500'
                  : 'border-gray-300 focus:ring-sky-500 focus:border-sky-500'
              }`}
              placeholder="Explique el motivo de la devolución (mín. 10 caracteres)"
            />
          )}
        />
        {errors.reason && (
          <span className="text-red-500 text-sm" role="alert">{errors.reason.message}</span>
        )}
      </div>
    </>
  );
}
export default RefundFormFields;