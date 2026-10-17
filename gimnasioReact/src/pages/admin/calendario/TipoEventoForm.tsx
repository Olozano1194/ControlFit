import { useForm } from 'react-hook-form';
import { useEffect, useState } from 'react';
import { toast } from 'react-hot-toast';
import {
    createTipoEvento,
    updateTipoEvento,
} from '../../../api/action/calendario.api';
import {
    TipoEvento,
    CreateTipoEventoDto,
} from '../../../model/calendario.model';
import { Input, Label } from '../../../components/ui/index';
import { getApiErrorMessage } from '../../../utils/apiError';
import ModalWrapper from './eventForm/ModalWrapper';

// ─── Props ───────────────────────────────────────────────────────────────────

interface TipoEventoFormProps {
    isOpen: boolean;
    onClose: () => void;
    tipo?: TipoEvento | null;
    onSuccess: () => void;
}

interface FormData {
    nombre: string;
    color: string;
}

// ─── Componente ──────────────────────────────────────────────────────────────

const DEFAULT_COLOR = '#3B82F6';

const TipoEventoForm = ({
    isOpen,
    onClose,
    tipo,
    onSuccess,
}: TipoEventoFormProps) => {
    const isEditing = !!tipo;
    const [isSubmitting, setIsSubmitting] = useState(false);
    const {
        register,
        handleSubmit,
        formState: { errors },
        reset,
        watch,
    } = useForm<FormData>({
        defaultValues: {
            nombre: '',
            color: DEFAULT_COLOR,
        },
    });

    const selectedColor = watch('color');

    // ── Reset del formulario ─────────────────────────────────────────────────

    useEffect(() => {
        if (!isOpen) return;
        if (tipo) {
            reset({ nombre: tipo.nombre, color: tipo.color });
        } else {
            reset({ nombre: '', color: DEFAULT_COLOR });
        }
    }, [isOpen, tipo, reset]);

    // ── Submit ───────────────────────────────────────────────────────────────

    const onSubmit = handleSubmit(async (data: FormData) => {
        setIsSubmitting(true);
        try {
            const dto: CreateTipoEventoDto = {
                nombre: data.nombre,
                color: data.color,
            };

            if (isEditing && tipo) {
                await updateTipoEvento(tipo.id, dto);
                toast.success('Tipo actualizado correctamente');
            } else {
                await createTipoEvento(dto);
                toast.success('Tipo creado correctamente');
            }
            onSuccess();
            onClose();
        } catch (error: unknown) {
            const err = error as { response?: { status?: number } };
            if (err?.response?.status === 400) {
                toast.error(
                    'Ya existe un tipo con ese nombre en este gimnasio'
                );
            } else {
                toast.error(getApiErrorMessage(error, 'Error al guardar el tipo'));
            }
        } finally {
            setIsSubmitting(false);
        }
    });

    if (!isOpen) return null;

    // ── Render ───────────────────────────────────────────────────────────────

    return (
        <ModalWrapper
            title={isEditing ? 'Editar Tipo de Evento' : 'Nuevo Tipo de Evento'}
            onClose={onClose}
        >
            <form onSubmit={onSubmit} className="space-y-6">
                {/* Nombre */}
                <div className="relative pt-5">
                    <Input
                        id="nombre"
                        type="text"
                        placeholder=""
                        aria-invalid={!!errors.nombre}
                        aria-describedby={errors.nombre ? 'nombre-error' : undefined}
                        {...register('nombre', {
                            required: {
                                value: true,
                                message: 'El nombre es requerido',
                            },
                            minLength: {
                                value: 2,
                                message: 'Mínimo 2 caracteres',
                            },
                            maxLength: {
                                value: 50,
                                message: 'Máximo 50 caracteres',
                            },
                        })}
                    />
                    <Label htmlFor="nombre">Nombre *</Label>
                    {errors.nombre && (
                        <span id="nombre-error" className="text-red-500 text-sm" role="alert">
                            {errors.nombre.message}
                        </span>
                    )}
                </div>

                {/* Color picker */}
                <div className="relative pt-5">
                    <div className="flex items-center gap-4">
                        <input
                            id="color"
                            type="color"
                            aria-invalid={!!errors.color}
                            aria-describedby={errors.color ? 'color-error' : undefined}
                            {...register('color', {
                                required: {
                                    value: true,
                                    message: 'El color es requerido',
                                },
                            })}
                            className="w-12 h-12 rounded-lg cursor-pointer border border-outline-variant/20"
                        />
                        <span className="font-mono text-sm text-secondary">
                            {selectedColor || DEFAULT_COLOR}
                        </span>
                    </div>
                    <Label htmlFor="color">Color *</Label>
                    {errors.color && (
                        <span id="color-error" className="text-red-500 text-sm" role="alert">
                            {errors.color.message}
                        </span>
                    )}
                </div>

                {/* Preview visual */}
                <div className="flex items-center gap-3 p-3 rounded-lg bg-surface-container-high">
                    <span
                        className="inline-block w-8 h-8 rounded-full border border-outline-variant/20"
                        style={{ backgroundColor: selectedColor || DEFAULT_COLOR }}
                    />
                    <span className="text-sm text-on-surface">
                        Vista previa del color
                    </span>
                </div>

                {/* Actions */}
                <div className="flex gap-3 pt-4 border-t border-surface-container-high">
                    <button
                        type="button"
                        onClick={onClose}
                        className="flex-1 bg-surface-container-high cursor-pointer font-semibold px-4 py-2 rounded-lg text-sm text-on-surface transition-colors hover:bg-surface-container-high/80"
                    >
                        Cancelar
                    </button>
                    <button
                        type="submit"
                        disabled={isSubmitting}
                        className="flex-1 bg-sky-600 cursor-pointer font-semibold px-4 py-2 rounded-lg text-sm text-white transition-colors hover:bg-sky-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isSubmitting
                            ? 'Guardando...'
                            : isEditing
                              ? 'Actualizar'
                              : 'Crear Tipo'}
                    </button>
                </div>
            </form>
        </ModalWrapper>
    );
};

export default TipoEventoForm;
