import type { FieldErrors, UseFormRegister } from 'react-hook-form';
import { Input, Label } from '../../../../components/ui/index';
import type { FormData } from './eventTypes';

interface EventDateFieldsProps {
    register: UseFormRegister<FormData>;
    errors: FieldErrors<FormData>;
}

const EventDateFields = ({ register, errors }: EventDateFieldsProps) => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="relative pt-5">
            <Input
                id="fecha_inicio"
                type="datetime-local"
                placeholder=""
                aria-invalid={!!errors.fecha_inicio}
                aria-describedby={errors.fecha_inicio ? 'fecha_inicio-error' : undefined}
                {...register('fecha_inicio', { required: { value: true, message: 'La fecha de inicio es obligatoria' } })}
            />
            <Label htmlFor="fecha_inicio">Fecha de inicio</Label>
            {errors.fecha_inicio && (
                <span id="fecha_inicio-error" className="text-red-500 text-sm" role="alert">
                    {errors.fecha_inicio.message}
                </span>
            )}
        </div>
        <div className="relative pt-5">
            <Input
                id="fecha_fin"
                type="datetime-local"
                placeholder=""
                aria-invalid={!!errors.fecha_fin}
                aria-describedby={errors.fecha_fin ? 'fecha_fin-error' : undefined}
                {...register('fecha_fin', { required: { value: true, message: 'La fecha de fin es obligatoria' } })}
            />
            <Label htmlFor="fecha_fin">Fecha de fin</Label>
            {errors.fecha_fin && (
                <span id="fecha_fin-error" className="text-red-500 text-sm" role="alert">
                    {errors.fecha_fin.message}
                </span>
            )}
        </div>
    </div>
)
export default EventDateFields;
