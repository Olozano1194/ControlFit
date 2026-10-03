import { useRefundModal } from './useRefundModal';
import { RefundFormFields } from './RefundFormFields';
import { RefundPreview } from './RefundPreview';
import Button from '@/components/ui/Button';
import type { AsignarMemberShips } from '@/model/asignarMemberShips.model';

interface RefundModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  asignacion: AsignarMemberShips | null;
}

export function RefundModal({
  isOpen,
  onClose,
  onSuccess,
  asignacion,
}: RefundModalProps) {
  const {
    isSubmitting,
    previewRemainingBalance,
    errors,
    control,
    handleSubmit,
    onSubmit,
  } = useRefundModal({ asignacion, onSuccess, onClose });

  if (!isOpen || !asignacion) return null;

  const currentSaldoPendiente = parseFloat(asignacion.saldo_pendiente as unknown as string) || 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Registrar Devolución</h2>
          <p className="text-sm text-gray-600 mt-1">
            Miembro: {asignacion.miembro_details?.name} {asignacion.miembro_details?.lastname}
          </p>
          <p className="text-sm text-gray-600">
            Plan: {asignacion.membresia_details?.name} | Saldo pendiente: ${currentSaldoPendiente.toLocaleString('es-CO', { minimumFractionDigits: 2 })}
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-5">
          <RefundFormFields
            control={control}
            errors={errors}
          />

          <RefundPreview
            previewRemainingBalance={previewRemainingBalance}
            currentSaldoPendiente={currentSaldoPendiente}
          />

          <div className="flex gap-3 justify-end pt-4 border-t border-gray-200">
            <Button
              type="button"
              variant="secondary"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Registrando...' : 'Registrar Devolución'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
export default RefundModal;