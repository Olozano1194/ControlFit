import { Controller, type Control, type FieldErrors } from 'react-hook-form';
import Input from '@/components/ui/Input';
import Label from '@/components/ui/Label';
import type { SuspenderFormData } from './useSuspenderModal';

interface SuspenderFormFieldsProps {
  control: Control<SuspenderFormData>;
  errors: FieldErrors<SuspenderFormData>;
}

export function SuspenderFormFields({
  control,
  errors,
}: SuspenderFormFieldsProps) {
  return (
    <>
      <div>
        <Label htmlFor="fecha_inicio">Fecha inicio suspensión (opcional)</Label>
        <Controller
          name="fecha_inicio"
          control={control}
          render={({ field }) => (
            <Input
              id="fecha_inicio"
              type="date"
              {...field}
              value={field.value}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                field.onChange(e.target.value);
              }}
              className="mt-1 w-full"
            />
          )}
        />
        {errors.fecha_inicio && (
          <span className="text-red-500 text-sm" role="alert">{errors.fecha_inicio.message}</span>
        )}
      </div>

      <div>
        <Label htmlFor="fecha_fin">Fecha fin suspensión (opcional)</Label>
        <Controller
          name="fecha_fin"
          control={control}
          render={({ field }) => (
            <Input
              id="fecha_fin"
              type="date"
              {...field}
              value={field.value}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                field.onChange(e.target.value);
              }}
              className="mt-1 w-full"
            />
          )}
        />
        {errors.fecha_fin && (
          <span className="text-red-500 text-sm" role="alert">{errors.fecha_fin.message}</span>
        )}
      </div>

      <div>
        <Label htmlFor="dias">Días de suspensión (alternativo a fechas)</Label>
        <Controller
          name="dias"
          control={control}
          render={({ field }) => (
            <Input
              id="dias"
              type="number"
              min="1"
              {...field}
              value={field.value}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                field.onChange(e.target.value);
              }}
              className="mt-1 w-full"
              placeholder="Ej: 30"
            />
          )}
        />
        {errors.dias && (
          <span className="text-red-500 text-sm" role="alert">{errors.dias.message}</span>
        )}
        <p className="text-xs text-gray-500 mt-1">
          Proporcione días O ambas fechas (inicio y fin)
        </p>
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
              placeholder="Explique el motivo de la suspensión (mín. 10 caracteres)"
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
export default SuspenderFormFields;