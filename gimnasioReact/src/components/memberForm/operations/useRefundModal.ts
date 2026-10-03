import { useState, useCallback, useMemo } from 'react';
import { useForm, Controller, type Control, type FieldErrors } from 'react-hook-form';
import { toast } from 'react-hot-toast';
import { axiosPrivate } from '@/api/axios/axios.private';
import type { AsignarMemberShips } from '@/model/asignarMemberShips.model';

export interface RefundFormData {
  monto: string;
  reason: string;
}

interface UseRefundModalProps {
  asignacion: AsignarMemberShips | null;
  onSuccess: () => void;
  onClose: () => void;
}

interface UseRefundModalReturn {
  isSubmitting: boolean;
  previewRemainingBalance: string;
  errors: FieldErrors<RefundFormData>;
  control: Control<RefundFormData>;
  handleSubmit: (onSubmit: (data: RefundFormData) => void) => (e?: React.BaseSyntheticEvent) => Promise<void>;
  Controller: typeof Controller;
  onSubmit: (data: RefundFormData) => Promise<void>;
}

export function useRefundModal({
  asignacion,
  onSuccess,
  onClose,
}: UseRefundModalProps): UseRefundModalReturn {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [previewRemainingBalance, setPreviewRemainingBalance] = useState<string>('');

  const {
    handleSubmit,
    watch,
    setError,
    clearErrors,
    control,
    formState: { errors },
  } = useForm<RefundFormData>({
    defaultValues: {
      monto: '',
      reason: '',
    },
  });

  const monto = watch('monto');

  // Calculate preview of remaining balance after refund
  const calculatePreview = useCallback(() => {
    if (!asignacion) return;

    const montoValue = parseFloat(monto) || 0;
    const saldoPendiente = parseFloat(asignacion.saldo_pendiente as unknown as string) || 0;

    if (montoValue > 0 && montoValue <= saldoPendiente) {
      const remaining = saldoPendiente - montoValue;
      setPreviewRemainingBalance(remaining.toFixed(2));
    } else {
      setPreviewRemainingBalance('');
    }
  }, [asignacion, monto]);

  // Update preview when inputs change
  useMemo(() => {
    calculatePreview();
  }, [calculatePreview]);

  const onSubmit = async (data: RefundFormData) => {
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

      // Validate monto
      const montoValue = parseFloat(data.monto);
      if (isNaN(montoValue) || montoValue <= 0) {
        setError('monto', {
          type: 'manual',
          message: 'El monto debe ser un número mayor a 0',
        });
        setIsSubmitting(false);
        return;
      }

      const saldoPendiente = parseFloat(asignacion.saldo_pendiente as unknown as string) || 0;
      if (montoValue > saldoPendiente) {
        setError('monto', {
          type: 'manual',
          message: `El monto no puede exceder el saldo pendiente (${saldoPendiente.toFixed(2)})`,
        });
        setIsSubmitting(false);
        return;
      }

      // Call backend API
      await axiosPrivate.post<AsignarMemberShips>(
        `/MemberShipsAsignada/${asignacion.id}/devolucion/`,
        {
          monto: montoValue,
          reason: data.reason.trim(),
        }
      );

      toast.success('Devolución registrada correctamente', {
        duration: 3000,
        position: 'bottom-right',
        style: { background: '#4b5563', color: '#fff', padding: '16px', borderRadius: '8px' },
      });

      onSuccess();
      onClose();
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Error al registrar la devolución';
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
    previewRemainingBalance,
    errors,
    control,
    handleSubmit,
    Controller,
    onSubmit,
  };
}
export default useRefundModal;