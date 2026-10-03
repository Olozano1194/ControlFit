import type { RenovarPreviewData } from '@/utils/renovarUtils';

interface RenovarPreviewProps {
  preview: RenovarPreviewData | null;
  currentDateFinal: string;
  currentPrice: number;
}

export function RenovarPreview({
  preview,
  currentDateFinal,
  currentPrice,
}: RenovarPreviewProps) {
  if (!preview || !preview.isValid) {
    return (
      <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
        <p className="text-sm text-gray-600">
          Complete los campos para ver la vista previa de la renovación.
        </p>
      </div>
    );
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr + 'T00:00:00');
    return date.toLocaleDateString('es-CO', { day: '2-digit', month: '2-digit', year: 'numeric' });
  };

  return (
    <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
      <h3 className="text-sm font-medium text-blue-800 mb-3">Vista previa de la renovación</h3>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="p-3 bg-white rounded border">
          <p className="text-xs text-gray-500">Fecha final actual</p>
          <p className="font-medium text-gray-900">{currentDateFinal}</p>
        </div>
        <div className="p-3 bg-white rounded border">
          <p className="text-xs text-gray-500">Nueva fecha inicio</p>
          <p className="font-medium text-blue-900">{formatDate(preview.dateInitial)}</p>
        </div>
        <div className="p-3 bg-white rounded border">
          <p className="text-xs text-gray-500">Precio actual</p>
          <p className="font-medium text-gray-900">${currentPrice.toLocaleString('es-CO', { minimumFractionDigits: 2 })}</p>
        </div>
        <div className="p-3 bg-white rounded border">
          <p className="text-xs text-gray-500">Nuevo precio</p>
          <p className="font-medium text-blue-900">${preview.price.toLocaleString('es-CO', { minimumFractionDigits: 2 })}</p>
        </div>
        <div className="p-3 bg-white rounded border col-span-2">
          <p className="text-xs text-gray-500">Nueva fecha final</p>
          <p className="font-medium text-blue-900">{formatDate(preview.dateFinal)} ({preview.totalDays} días)</p>
        </div>
      </div>

      <p className="text-xs text-blue-700">
        Se creará una <strong>nueva asignación</strong> independiente. La asignación actual se mantiene como historial.
        El estado de pago de la nueva asignación será <strong>Pendiente</strong> (sin pagos registrados).
      </p>
    </div>
  );
}
export default RenovarPreview;