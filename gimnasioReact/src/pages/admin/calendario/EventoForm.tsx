import { useForm } from 'react-hook-form';
import { useEffect, useState } from 'react';
import { toast } from 'react-hot-toast';
import { createEvento, updateEvento, getTiposEvento } from '../../../api/action/calendario.api';
import { TipoEvento, CreateEventoDto, UpdateEventoDto } from '../../../model/calendario.model';
import { Input, Label, Select } from '../../../components/ui/index';
import { getApiErrorMessage } from '../../../utils/apiError';
import { toLocalInputValue } from './dateTime';
// types
import { EventoFormProps, FormData } from './eventForm/eventTypes';
import EventFormActions from './eventForm/EventFormActions';
import EventDateFields from './eventForm/EventDateFields';
import ModalWrapper from './eventForm/ModalWrapper';


// ─── Componente ──────────────────────────────────────────────────────────────
const EventoForm = ({ isOpen, onClose, event, onSuccess, initialDates }: EventoFormProps) => {
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

    // Se dependen los VALORES del prefill, no el objeto: el padre lo crea inline
    // en el JSX, así que su identidad cambia en cada render y resetearía el
    // formulario mientras el usuario escribe.
    const prefillStart = initialDates?.start;
    const prefillEnd = initialDates?.end;

    useEffect(() => {
        if (!isOpen) return;
        if (event) {
            reset({
                titulo: event.titulo,
                fecha_inicio: toLocalInputValue(new Date(event.fecha_inicio)),
                fecha_fin: toLocalInputValue(new Date(event.fecha_fin)),
                descripcion: event.descripcion || '',
                tipo: event.tipo?.toString() || '',
                relacion_tipo: event.relacion_tipo || '',
                relacion_id: event.relacion_id?.toString() || '',
            });
        } else if (prefillStart && prefillEnd) {
            // Prefill desde el slot clickeado (creación) — ya viene en hora local
            reset({
                titulo: '',
                fecha_inicio: prefillStart.slice(0, 16),
                fecha_fin: prefillEnd.slice(0, 16),
                descripcion: '',
                tipo: '',
                relacion_tipo: '',
                relacion_id: '',
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
    }, [isOpen, event, reset, prefillStart, prefillEnd]);

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
            toast.error(getApiErrorMessage(error, 'Error al guardar el evento'));
        } finally {
            setIsSubmitting(false);
        }
    });

    if (!isOpen) return null;

    // ── Render ───────────────────────────────────────────────────────────────
    return (
        <ModalWrapper title={isEditing ? 'Editar Evento' : 'Nuevo Evento'} onClose={onClose}>
            {/* Formulario */}
            <form onSubmit={onSubmit} className="space-y-6">
                {/* Título */}
                <div className="relative pt-5">
                    <Input
                        id="titulo"
                        type="text"
                        placeholder=""
                        aria-invalid={!!errors.titulo}
                        aria-describedby={errors.titulo ? 'titulo-error' : undefined}
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
                    <Label htmlFor="titulo">Título *</Label>
                    {errors.titulo && (
                        <span id="titulo-error" className="text-red-500 text-sm" role="alert">
                            {errors.titulo.message}
                        </span>
                    )}
                </div>
                {/* Fechas */}
                <EventDateFields register={register} errors={errors} />
                {/* Descripción */}
                <div className="relative pt-5">
                    <textarea
                        id="descripcion"
                        {...register('descripcion')}
                        className="floating-input border-b border-b-[rgba(195,198,215,0.4)] bg-transparent font-medium outline-none px-0 rounded-none text-on-surface w-full focus:ring-0 focus:border-text-primary min-h-20 resize-y"
                        placeholder=""
                        rows={3}
                    />
                    <Label htmlFor="descripcion">Descripción</Label>
                </div>
                {/* Tipo */}
                <div className="relative pt-5">
                    <Select id="tipo" {...register('tipo')}>
                        <option value="">Sin tipo</option>
                        {tipos.map((t) => (
                            <option key={t.id} value={t.id}>
                                {t.nombre}
                            </option>
                        ))}
                    </Select>
                    <Label htmlFor="tipo">Tipo de Evento</Label>
                </div>
                {/* Relación opcional */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="relative pt-5">
                        <Select id="relacion_tipo" {...register('relacion_tipo')}>
                            <option value="">Ninguna</option>
                            <option value="miembro">Miembro</option>
                            <option value="membresia">Membresía</option>
                            <option value="suplemento">Suplemento</option>
                        </Select>
                        <Label htmlFor="relacion_tipo">Relacionado a</Label>
                    </div>
                    <div className="relative pt-5">
                        <Input
                            id="relacion_id"
                            type="number"
                            placeholder=""
                            {...register('relacion_id')}
                        />
                        <Label htmlFor="relacion_id">ID de relación</Label>
                    </div>
                </div>
                {/* Actions */}
                <EventFormActions
                    isSubmitting={isSubmitting}
                    isEditing={isEditing}
                    onClose={onClose}
                />
            </form>            
        </ModalWrapper>
    );
};
export default EventoForm;
