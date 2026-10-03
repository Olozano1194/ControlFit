import { useSuspenderModal } from './useSuspenderModal';
import { SuspenderFormFields } from './SuspenderFormFields';
import { SuspenderPreview } from './SuspenderPreview';
import Button from '@/components/ui/Button';
import type { AsignarMemberShips } from '@/model/asignarMemberShips.model';

interface SuspenderMembresiaModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  asignacion: AsignarMemberShips | null;
}

export function SuspenderMembresiaModal({
  isOpen,
  onClose,
  onSuccess,
  asignacion,
}: SuspenderMembresiaModalProps) {
  const {
    isSubmitting,
    previewDateFinal,
    errors,
    control,
    handleSubmit,
    onSubmit,
  } = useSuspenderModal({ asignacion, onSuccess, onClose });

  if (!isOpen || !asignacion) return null;

  const currentDateFinal = asignacion.dateFinal;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Suspender Membresía</h2>
          <p className="text-sm text-gray-600 mt-1">
            Miembro: {asignacion.miembro_details?.name} {asignacion.miembro_details?.lastname}
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-5">
          <SuspenderFormFields
            control={control}
            errors={errors}
          />

          <SuspenderPreview
            previewDateFinal={previewDateFinal}
            currentDateFinal={currentDateFinal}
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
              {isSubmitting ? 'Suspendiendo...' : 'Suspender'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
export default SuspenderMembresiaModal;