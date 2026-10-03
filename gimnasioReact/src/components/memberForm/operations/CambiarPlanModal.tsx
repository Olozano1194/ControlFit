import { useCambiarPlanModal } from './useCambiarPlanModal';
import { CambiarPlanFormFields } from './CambiarPlanFormFields';
import { CambiarPlanPreview } from './CambiarPlanPreview';
import Button from '@/components/ui/Button';
import type { AsignarMemberShips } from '@/model/asignarMemberShips.model';
import type { Membresia } from '@/model/memberShips.model';

interface CambiarPlanModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  asignacion: AsignarMemberShips | null;
  membresias: Membresia[];
}

export function CambiarPlanModal({
  isOpen,
  onClose,
  onSuccess,
  asignacion,
  membresias,
}: CambiarPlanModalProps) {
  const {
    isSubmitting,
    preview,
    errors,
    control,
    handleSubmit,
    onSubmit,
  } = useCambiarPlanModal({ asignacion, membresias, onSuccess, onClose });

  if (!isOpen || !asignacion) return null;

  const currentDateFinal = asignacion.dateFinal;
  const currentPrice = parseFloat(asignacion.price as unknown as string) || 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Cambiar Plan de Membresía</h2>
          <p className="text-sm text-gray-600 mt-1">
            Miembro: {asignacion.miembro_details?.name} {asignacion.miembro_details?.lastname}
          </p>
          <p className="text-sm text-gray-600">
            Plan actual: {asignacion.membresia_details?.name} | Fecha final: {currentDateFinal}
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-5">
          <CambiarPlanFormFields
            control={control}
            errors={errors}
            membresias={membresias}
          />

          <CambiarPlanPreview
            preview={preview}
            currentDateFinal={currentDateFinal}
            currentPrice={currentPrice}
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
              {isSubmitting ? 'Cambiando plan...' : 'Cambiar Plan'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
export default CambiarPlanModal;