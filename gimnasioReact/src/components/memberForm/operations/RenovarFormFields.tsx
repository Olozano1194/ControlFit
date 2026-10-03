import { Controller, type Control, type FieldErrors } from 'react-hook-form';
import Input from '@/components/ui/Input';
import Label from '@/components/ui/Label';
import Select from '@/components/ui/Select';
import type { RenovarFormData } from './useRenovarModal';
import type { Membresia } from '@/model/memberShips.model';

interface RenovarFormFieldsProps {
  control: Control<RenovarFormData>;
  errors: FieldErrors<RenovarFormData>;
  membresias: Membresia[];
}

export function RenovarFormFields({
  control,
  errors,
  membresias,
}: RenovarFormFieldsProps) {
  // Filter out inactive memberships for renewal
  const activeMembresias = membresias.filter(m => m.is_active);

  return (
    <>
      <div>
        <Label htmlFor="membresia_id">Membresía para renovación <span className="text-red-500">*</span></Label>
        <Controller
          name="membresia_id"
          control={control}
          rules={{ required: { value: true, message: 'Debe seleccionar una membresía' } }}
          render={({ field }) => (
            <Select
              id="membresia_id"
              {...field}
              value={field.value}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => {
                field.onChange(e.target.value);
              }}
              className={`mt-1 w-full ${errors.membresia_id ? 'border-red-500 focus:ring-red-500 focus:border-red-500' : 'border-gray-300 focus:ring-sky-500 focus:border-sky-500'}`}
            >
              <option value="">Seleccione una membresía</option>
              {activeMembresias.map((membresia) => (
                <option key={membresia.id} value={membresia.id.toString()}>
                  {membresia.name} - ${membresia.price.toLocaleString('es-CO')} ({membresia.duration} días)
                </option>
              ))}
            </Select>
          )}
        />
        {errors.membresia_id && (
          <span className="text-red-500 text-sm" role="alert">{errors.membresia_id.message}</span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
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
                step="1"
                {...field}
                value={field.value}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                  field.onChange(e.target.value);
                }}
                className={`mt-1 w-full ${errors.multiplier ? 'border-red-500 focus:ring-red-500 focus:border-red-500' : 'border-gray-300 focus:ring-sky-500 focus:border-sky-500'}`}
                placeholder="1"
              />
            )}
          />
          {errors.multiplier && (
            <span className="text-red-500 text-sm" role="alert">{errors.multiplier.message}</span>
          )}
        </div>

        <div>
          <Label htmlFor="discount_percent">Descuento (%)</Label>
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
                className={`mt-1 w-full ${errors.discount_percent ? 'border-red-500 focus:ring-red-500 focus:border-red-500' : 'border-gray-300 focus:ring-sky-500 focus:border-sky-500'}`}
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
              placeholder="Explique el motivo de la renovación (mín. 10 caracteres)"
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
export default RenovarFormFields;