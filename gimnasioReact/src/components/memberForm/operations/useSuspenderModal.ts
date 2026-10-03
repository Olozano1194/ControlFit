import { useState, useCallback, useMemo } from 'react';
import { useForm, Controller, type Control, type FieldErrors } from 'react-hook-form';
import { toast } from 'react-hot-toast';
import { axiosPrivate } from '@/api/axios/axios.private';
import type { AsignarMemberShips } from '@/model/asignarMemberShips.model';

export interface SuspenderFormData {
  fecha_inicio: string;
  fecha_fin: string;
  dias: string;
  reason: string;
}

interface UseSuspenderModalProps {
  asignacion: AsignarMemberShips | null;
  onSuccess: () => void;
  onClose: () => void;
}

interface UseSuspenderModalReturn {
  isSubmitting: boolean;
  previewDateFinal: string;
  errors: FieldErrors<SuspenderFormData>;
  control: Control<SuspenderFormData>;
  handleSubmit: (onSubmit: (data: SuspenderFormData) => void) => (e?: React.BaseSyntheticEvent) => Promise<void>;
  Controller: typeof Controller;
  onSubmit: (data: SuspenderFormData) => Promise<void>;
}

export function useSuspenderModal({
  asignacion,
  onSuccess,
  onClose,
}: UseSuspenderModalProps): UseSuspenderModalReturn {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [previewDateFinal, setPreviewDateFinal] = useState<string>('');

  const {
    handleSubmit,
    watch,
    setError,
    clearErrors,
    control,
    formState: { errors },
  } = useForm<SuspenderFormData>({
    defaultValues: {
      fecha_inicio: '',
      fecha_fin: '',
      dias: '',
      reason: '',
    },
  });

  const fechaInicio = watch('fecha_inicio');
  const fechaFin = watch('fecha_fin');
  const dias = watch('dias');

  // Calculate preview of new dateFinal
  const calculatePreview = useCallback(() => {
    if (!asignacion) return;

    let suspensionDays = 0;
    if (dias) {
      const d = parseInt(dias, 10);
      if (!isNaN(d) && d > 0) {
        suspensionDays = d;
      }
    } else if (fechaInicio && fechaFin) {
      const start = new Date(fechaInicio);
      const end = new Date(fechaFin);
      if (!isNaN(start.getTime()) && !isNaN(end.getTime()) && end > start) {
        suspensionDays = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
      }
    }

    if (suspensionDays > 0) {
      const currentFinal = new Date(asignacion.dateFinal);
      const newFinal = new Date(currentFinal);
      newFinal.setDate(newFinal.getDate() + suspensionDays);
      setPreviewDateFinal(newFinal.toISOString().split('T')[0]);
    } else {
      setPreviewDateFinal('');
    }
  }, [asignacion, dias, fechaInicio, fechaFin]);

  // Update preview when inputs change
  useMemo(() => {
    calculatePreview();
  }, [calculatePreview]);

  const onSubmit = async (data: SuspenderFormData) => {
    if (!asignacion) return;

    setIsSubmitting(true);
    clearErrors();

    try {
      // Validate reason
      if (!data.reason || data.reason.trim().length < 10) {
        setError('reason', {
          type: 'manual',
          message: 'El motivo debe tener al menos 10 caracteres',
        });
        setIsSubmitting(false);
        return;
      }

      // Validate suspension data
      let suspensionDays = 0;
      if (data.dias) {
        suspensionDays = parseInt(data.dias, 10);
        if (isNaN(suspensionDays) || suspensionDays <= 0) {
          setError('dias', {
            type: 'manual',
            message: 'Los días deben ser un número positivo',
          });
          setIsSubmitting(false);
          return;
        }
      } else if (data.fecha_inicio && data.fecha_fin) {
        const start = new Date(data.fecha_inicio);
        const end = new Date(data.fecha_fin);
        if (isNaN(start.getTime()) || isNaN(end.getTime()) || end <= start) {
          setError('fecha_fin', {
            type: 'manual',
            message: 'La fecha de fin debe ser posterior a la fecha de inicio',
          });
          setIsSubmitting(false);
          return;
        }
        suspensionDays = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
      } else {
        setError('dias', {
          type: 'manual',
          message: 'Debe proporcionar días o ambas fechas',
        });
        setIsSubmitting(false);
        return;
      }

      // Call backend API
      await axiosPrivate.post<AsignarMemberShips>(
        `/MemberShipsAsignada/${asignacion.id}/suspender/`,
        {
          fecha_inicio: data.fecha_inicio || undefined,
          fecha_fin: data.fecha_fin || undefined,
          dias: suspensionDays,
          reason: data.reason.trim(),
        }
      );

      toast.success('Membresía suspendida correctamente', {
        duration: 3000,
        position: 'bottom-right',
        style: { background: '#4b5563', color: '#fff', padding: '16px', borderRadius: '8px' },
      });

      onSuccess();
      onClose();
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Error al suspender la membresía';
      if (err && typeof err === 'object' && 'response' in err) {
        const errResponse = (err as { response?: { data?: Record<string, string[]> } }).response;
        if (errResponse?.data) {
          const firstError = Object.values(errResponse.data)[0];
          if (Array.isArray(firstError) && firstError.length > 0) {
            toast.error(firstError[0]);
            setIsSubmitting(false);
            return;
          }
        }
      }
      toast.error(`Error: ${errorMessage}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return {
    isSubmitting,
    previewDateFinal,
    errors,
    control,
    handleSubmit,
    Controller,
    onSubmit,
  };
}
export default useSuspenderModal;