import { Controller, type Control, type FieldErrors } from 'react-hook-form';
import Input from '@/components/ui/Input';
import Label from '@/components/ui/Label';
import type { CambiarPlanFormData } from './useCambiarPlanModal';
import type { Membresia } from '@/model/memberShips.model';

interface CambiarPlanFormFieldsProps {
  control: Control<CambiarPlanFormData>;
  errors: FieldErrors<CambiarPlanFormData>;
  membresias: Membresia[];
}

export function CambiarPlanFormFields({
  control,
  errors,
  membresias,
}: CambiarPlanFormFieldsProps) {
  return (
    <>
      <div>
        <Label htmlFor="nueva_membresia_id">Nueva Membresía <span className="text-red-500">*</span></Label>
        <Controller
          name="nueva_membresia_id"
          control={control}
          render={({ field }) => (
            <select
              id="nueva_membresia_id"
              {...field}
              value={field.value}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => {
                field.onChange(e.target.value);
              }}
              className={`mt-1 w-full rounded-lg border p-3 text-base ${
                errors.nueva_membresia_id
                  ? 'border-red-500 focus:ring-red-500 focus:border-red-500'
                  : 'border-gray-300 focus:ring-sky-500 focus:border-sky-500'
              }`}
            >
              <option value="">Seleccione una membresía</option>
              {membresias.map((m) => (
                <option key={m.id} value={m.id.toString()}>
                  {m.name} - ${m.price} - {m.duration} días (máx {m.max_multiplier}x)
                </option>
              ))}
            </select>
          )}
        />
        {errors.nueva_membresia_id && (
          <span className="text-red-500 text-sm" role="alert">{errors.nueva_membresia_id.message}</span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="multiplier">Multiplicador</Label>
          <Controller
            name="multiplier"
            control={control}
            render={({ field }) => (
              <Input
                id="multiplier"
                type="number"
                min="1"
                step="0.1"
                {...field}
                value={field.value}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                  field.onChange(e.target.value);
                }}
                className={`mt-1 w-full ${
                  errors.multiplier
                    ? 'border-red-500 focus:ring-red-500 focus:border-red-500'
                    : 'border-gray-300 focus:ring-sky-500 focus:border-sky-500'
                }`}
                placeholder="1"
              />
            )}
          />
          {errors.multiplier && (
            <span className="text-red-500 text-sm" role="alert">{errors.multiplier.message}</span>
          )}
        </div>

        <div>
          <Label htmlFor="discount_percent">Descuento %</Label>
          <Controller
            name="discount_percent"
            control={control}
            render={({ field }) => (
              <Input
                id="discount_percent"
                type="number"
                min="0"
                max="100"
                step="0.01"
                {...field}
                value={field.value}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                  field.onChange(e.target.value);
                }}
                className={`mt-1 w-full ${
                  errors.discount_percent
                    ? 'border-red-500 focus:ring-red-500 focus:border-red-500'
                    : 'border-gray-300 focus:ring-sky-500 focus:border-sky-500'
                }`}
                placeholder="0"
              />
            )}
          />
          {errors.discount_percent && (
            <span className="text-red-500 text-sm" role="alert">{errors.discount_percent.message}</span>
          )}
        </div>
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
              placeholder="Explique el motivo del cambio de plan (mín. 10 caracteres)"
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
export default CambiarPlanFormFields;