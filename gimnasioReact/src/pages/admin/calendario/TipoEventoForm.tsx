import { useForm } from 'react-hook-form';
import { useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { IoClose } from 'react-icons/io5';
import {
    createTipoEvento,
    updateTipoEvento,
} from '../../../api/action/calendario.api';
import {
    TipoEvento,
    CreateTipoEventoDto,
} from '../../../model/calendario.model';
import { Input, Label } from '../../../components/ui/index';

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
                const msg =
                    error instanceof Error
                        ? error.message
                        : 'Error al guardar el tipo';
                toast.error(msg);
            }
        }
    });

    if (!isOpen) return null;

    // ── Render ───────────────────────────────────────────────────────────────

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
            <div className="bg-surface-container-lowest rounded-xl shadow-2xl w-full max-w-md mx-4 p-6 relative">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-bold text-on-surface">
                        {isEditing
                            ? 'Editar Tipo de Evento'
                            : 'Nuevo Tipo de Evento'}
                    </h3>
                    <button
                        onClick={onClose}
                        className="text-secondary cursor-pointer hover:text-on-surface transition-colors"
                        aria-label="Cerrar"
                    >
                        <IoClose size={24} />
                    </button>
                </div>

                <form onSubmit={onSubmit} className="space-y-6">
                    {/* Nombre */}
                    <div className="relative pt-5">
                        <Input
                            type="text"
                            placeholder=""
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
                        <Label>Nombre *</Label>
                        {errors.nombre && (
                            <span className="text-red-500 text-sm">
                                {errors.nombre.message}
                            </span>
                        )}
                    </div>

                    {/* Color picker */}
                    <div className="relative pt-5">
                        <div className="flex items-center gap-4">
                            <input
                                type="color"
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
                        <Label>Color *</Label>
                        {errors.color && (
                            <span className="text-red-500 text-sm">
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
                            className="flex-1 bg-sky-600 cursor-pointer font-semibold px-4 py-2 rounded-lg text-sm text-white transition-colors hover:bg-sky-500"
                        >
                            {isEditing ? 'Actualizar' : 'Crear Tipo'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default TipoEventoForm;