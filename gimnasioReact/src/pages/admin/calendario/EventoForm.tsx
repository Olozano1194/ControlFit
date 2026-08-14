import { useForm } from 'react-hook-form';
import { useEffect, useState } from 'react';
import { toast } from 'react-hot-toast';
import { IoClose } from 'react-icons/io5';
import {
    createEvento,
    updateEvento,
    getTiposEvento,
} from '../../../api/action/calendario.api';
import {
    EventoCalendario,
    TipoEvento,
    CreateEventoDto,
    UpdateEventoDto,
} from '../../../model/calendario.model';
import { Input, Label, Select } from '../../../components/ui/index';

// ─── Props ───────────────────────────────────────────────────────────────────

interface EventoFormProps {
    isOpen: boolean;
    onClose: () => void;
    event?: EventoCalendario | null;
    onSuccess: () => void;
}

interface FormData {
    titulo: string;
    fecha_inicio: string;
    fecha_fin: string;
    descripcion: string;
    tipo: string;
    relacion_tipo: string;
    relacion_id: string;
}

// ─── Componente ──────────────────────────────────────────────────────────────

const EventoForm = ({ isOpen, onClose, event, onSuccess }: EventoFormProps) => {
    const [tipos, setTipos] = useState<TipoEvento[]>([]);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const isEditing = !!event;

    const {
        register,
        handleSubmit,
        formState: { errors },
        reset,
    } = useForm<FormData>();

    // ── Cargar tipos al abrir ────────────────────────────────────────────────

    useEffect(() => {
        if (isOpen) {
            const fetchTipos = async () => {
                try {
                    const data = await getTiposEvento();
                    setTipos(data);
                } catch {
                    // Silencioso — CalendarioPage ya maneja errores
                }
            };
            fetchTipos();
        }
    }, [isOpen]);

    // ── Reset del formulario ─────────────────────────────────────────────────

    useEffect(() => {
        if (!isOpen) return;
        if (event) {
            reset({
                titulo: event.titulo,
                fecha_inicio: event.fecha_inicio.slice(0, 16),
                fecha_fin: event.fecha_fin.slice(0, 16),
                descripcion: event.descripcion || '',
                tipo: event.tipo?.toString() || '',
                relacion_tipo: event.relacion_tipo || '',
                relacion_id: event.relacion_id?.toString() || '',
            });
        } else {
            reset({
                titulo: '',
                fecha_inicio: '',
                fecha_fin: '',
                descripcion: '',
                tipo: '',
                relacion_tipo: '',
                relacion_id: '',
            });
        }
    }, [isOpen, event, reset]);

    // ── Submit ───────────────────────────────────────────────────────────────

    const onSubmit = handleSubmit(async (data: FormData) => {
        // Validación extra: fin >= inicio
        if (data.fecha_inicio && data.fecha_fin) {
            const inicio = new Date(data.fecha_inicio);
            const fin = new Date(data.fecha_fin);
            if (fin < inicio) {
                toast.error('La fecha de fin debe ser mayor o igual a la fecha de inicio');
                return;
            }
        }

        setIsSubmitting(true);
        try {
            const dto: CreateEventoDto = {
                titulo: data.titulo,
                fecha_inicio: new Date(data.fecha_inicio).toISOString(),
                fecha_fin: new Date(data.fecha_fin).toISOString(),
                descripcion: data.descripcion || '',
                tipo: data.tipo ? parseInt(data.tipo, 10) : null,
                relacion_tipo: data.relacion_tipo || '',
                relacion_id: data.relacion_id ? parseInt(data.relacion_id, 10) : null,
            };

            if (isEditing && event) {
                await updateEvento(event.id, dto as UpdateEventoDto);
                toast.success('Evento actualizado correctamente');
            } else {
                await createEvento(dto);
                toast.success('Evento creado correctamente');
            }
            onSuccess();
            onClose();
        } catch (error) {
            const msg =
                error instanceof Error ? error.message : 'Error al guardar el evento';
            toast.error(msg);
        } finally {
            setIsSubmitting(false);
        }
    });

    if (!isOpen) return null;

    // ── Render ───────────────────────────────────────────────────────────────

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
            <div className="bg-surface-container-lowest rounded-xl shadow-2xl w-full max-w-lg mx-4 p-6 relative max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-bold text-on-surface">
                        {isEditing ? 'Editar Evento' : 'Nuevo Evento'}
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
                    {/* Título */}
                    <div className="relative pt-5">
                        <Input
                            type="text"
                            placeholder=""
                            {...register('titulo', {
                                required: {
                                    value: true,
                                    message: 'El título es requerido',
                                },
                                minLength: {
                                    value: 3,
                                    message: 'El título debe tener al menos 3 caracteres',
                                },
                                maxLength: {
                                    value: 150,
                                    message: 'El título debe tener máximo 150 caracteres',
                                },
                            })}
                        />
                        <Label>Título *</Label>
                        {errors.titulo && (
                            <span className="text-red-500 text-sm">
                                {errors.titulo.message}
                            </span>
                        )}
                    </div>

                    {/* Fechas */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="relative pt-5">
                            <Input
                                type="datetime-local"
                                placeholder=""
                                {...register('fecha_inicio', {
                                    required: {
                                        value: true,
                                        message: 'Fecha de inicio requerida',
                                    },
                                })}
                            />
                            <Label>Fecha Inicio *</Label>
                            {errors.fecha_inicio && (
                                <span className="text-red-500 text-sm">
                                    {errors.fecha_inicio.message}
                                </span>
                            )}
                        </div>
                        <div className="relative pt-5">
                            <Input
                                type="datetime-local"
                                placeholder=""
                                {...register('fecha_fin', {
                                    required: {
                                        value: true,
                                        message: 'Fecha de fin requerida',
                                    },
                                })}
                            />
                            <Label>Fecha Fin *</Label>
                            {errors.fecha_fin && (
                                <span className="text-red-500 text-sm">
                                    {errors.fecha_fin.message}
                                </span>
                            )}
                        </div>
                    </div>

                    {/* Descripción */}
                    <div className="relative pt-5">
                        <textarea
                            {...register('descripcion')}
                            className="floating-input border-b border-b-[rgba(195,198,215,0.4)] bg-transparent font-medium outline-none px-0 rounded-none text-on-surface w-full focus:ring-0 focus:border-text-primary min-h-20 resize-y"
                            placeholder=""
                            rows={3}
                        />
                        <Label>Descripción</Label>
                    </div>

                    {/* Tipo */}
                    <div className="relative pt-5">
                        <Select {...register('tipo')}>
                            <option value="">Sin tipo</option>
                            {tipos.map((t) => (
                                <option key={t.id} value={t.id}>
                                    {t.nombre}
                                </option>
                            ))}
                        </Select>
                        <Label>Tipo de Evento</Label>
                    </div>

                    {/* Relación opcional */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="relative pt-5">
                            <Select {...register('relacion_tipo')}>
                                <option value="">Ninguna</option>
                                <option value="miembro">Miembro</option>
                                <option value="membresia">Membresía</option>
                                <option value="suplemento">Suplemento</option>
                            </Select>
                            <Label>Relacionado a</Label>
                        </div>
                        <div className="relative pt-5">
                            <Input
                                type="number"
                                placeholder=""
                                {...register('relacion_id')}
                            />
                            <Label>ID de relación</Label>
                        </div>
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
                                  : 'Crear Evento'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default EventoForm;