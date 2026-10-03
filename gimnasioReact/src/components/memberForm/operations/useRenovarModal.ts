import { useState, useCallback, useMemo } from 'react';
import { useForm, Controller, type Control, type FieldErrors } from 'react-hook-form';
import { toast } from 'react-hot-toast';
import { axiosPrivate } from '@/api/axios/axios.private';
import type { AsignarMemberShips } from '@/model/asignarMemberShips.model';
import type { Membresia } from '@/model/memberShips.model';
import { calculateRenovarPreview, type RenovarPreviewData } from '@/utils/renovarUtils';

export interface RenovarFormData {
  membresia_id: string;
  reason: string;
  multiplier: string;
  discount_percent: string;
}

interface UseRenovarModalProps {
  asignacion: AsignarMemberShips | null;
  membresias: Membresia[];
  onSuccess: () => void;
  onClose: () => void;
}

interface UseRenovarModalReturn {
  isSubmitting: boolean;
  preview: RenovarPreviewData | null;
  errors: FieldErrors<RenovarFormData>;
  control: Control<RenovarFormData>;
  handleSubmit: (onSubmit: (data: RenovarFormData) => void) => (e?: React.BaseSyntheticEvent) => Promise<void>;
  Controller: typeof Controller;
  onSubmit: (data: RenovarFormData) => Promise<void>;
}

export function useRenovarModal({
  asignacion,
  membresias,
  onSuccess,
  onClose,
}: UseRenovarModalProps): UseRenovarModalReturn {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [preview, setPreview] = useState<RenovarPreviewData | null>(null);

  const {
    handleSubmit,
    watch,
    setError,
    clearErrors,
    control,
    formState: { errors },
  } = useForm<RenovarFormData>({
    defaultValues: {
      membresia_id: '',
      reason: '',
      multiplier: '1',
      discount_percent: '0',
    },
  });

  const membresiaId = watch('membresia_id');
  const multiplier = watch('multiplier');
  const discountPercent = watch('discount_percent');

  // Find selected membership
  const selectedMembresia = useMemo(() => {
    if (!membresiaId) return null;
    return membresias.find(m => m.id === parseInt(membresiaId, 10)) || null;
  }, [membresiaId, membresias]);

  // Find current membership from the list
  const currentMembresia = useMemo(() => {
    const currentMembresiaId = asignacion?.membresia_details?.id;
    if (!currentMembresiaId) return null;
    return membresias.find(m => m.id === currentMembresiaId) || null;
  }, [asignacion?.membresia_details?.id, membresias]);

  // Calculate preview using extracted utility
  const calculatePreview = useCallback(() => {
    const mult = parseFloat(multiplier) || 1;
    const disc = parseFloat(discountPercent) || 0;
    setPreview(calculateRenovarPreview(asignacion, selectedMembresia, currentMembresia, mult, disc));
  }, [asignacion, selectedMembresia, currentMembresia, multiplier, discountPercent]);

  useMemo(() => {
    calculatePreview();
  }, [calculatePreview]);

  const onSubmit = async (data: RenovarFormData) => {
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

      // Validate membresia_id
      if (!data.membresia_id) {
        setError('membresia_id', {
          type: 'manual',
          message: 'Debe seleccionar una membresía para la renovación',
        });
        setIsSubmitting(false);
        return;
      }

      // Validate multiplier
      const mult = parseFloat(data.multiplier);
      if (isNaN(mult) || mult < 1) {
        setError('multiplier', {
          type: 'manual',
          message: 'El multiplicador debe ser al menos 1',
        });
        setIsSubmitting(false);
        return;
      }

      // Validate discount_percent
      const disc = parseFloat(data.discount_percent);
      if (isNaN(disc) || disc < 0 || disc > 100) {
        setError('discount_percent', {
          type: 'manual',
          message: 'El descuento debe estar entre 0 y 100',
        });
        setIsSubmitting(false);
        return;
      }

      // Validate max_multiplier
      if (selectedMembresia && mult > selectedMembresia.max_multiplier) {
        setError('multiplier', {
          type: 'manual',
          message: selectedMembresia.max_multiplier <= 1
            ? 'Esa membresía no se puede multiplicar'
            : `Esa membresía solo permite hasta ${selectedMembresia.max_multiplier} periodos`,
        });
        setIsSubmitting(false);
        return;
      }

      // Call backend API
      await axiosPrivate.post<AsignarMemberShips>(
        `/MemberShipsAsignada/${asignacion.id}/renovar/`,
        {
          membresia_id: parseInt(data.membresia_id, 10),
          reason: data.reason.trim(),
          multiplier: mult,
          discount_percent: disc,
        }
      );

      toast.success('Membresía renovada correctamente', {
        duration: 3000,
        position: 'bottom-right',
        style: { background: '#4b5563', color: '#fff', padding: '16px', borderRadius: '8px' },
      });

      onSuccess();
      onClose();
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Error al renovar la membresía';
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
    preview,
    errors,
    control,
    handleSubmit,
    Controller,
    onSubmit,
  };
}
export default useRenovarModal;