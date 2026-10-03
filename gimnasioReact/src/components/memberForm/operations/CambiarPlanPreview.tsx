import type { CambiarPlanPreviewData } from '@/utils/cambiarPlanUtils';

interface CambiarPlanPreviewProps {
  preview: CambiarPlanPreviewData | null;
  currentDateFinal: string;
  currentPrice: number;
}

export function CambiarPlanPreview({
  preview,
  currentDateFinal,
  currentPrice,
}: CambiarPlanPreviewProps) {
  if (!preview) return null;

  return (
    <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg space-y-3">
      <p className="text-sm font-medium text-emerald-800">Vista previa del cambio de plan</p>
      
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div>
          <p className="text-emerald-700">Fecha final actual:</p>
          <p className="font-medium">{currentDateFinal}</p>
        </div>
        <div>
          <p className="text-emerald-700">Nueva fecha final:</p>
          <p className="font-medium">{preview.newDateFinal}</p>
        </div>
        <div>
          <p className="text-emerald-700">Precio actual:</p>
          <p className="font-medium">${currentPrice.toLocaleString()}</p>
        </div>
        <div>
          <p className="text-emerald-700">Nuevo precio base:</p>
          <p className="font-medium">${preview.newPlanTotal.toLocaleString()}</p>
        </div>
      </div>

      <div className="bg-white border border-emerald-200 rounded p-3">
        <p className="text-sm text-emerald-700 mb-2">Cálculo del crédito por días no usados:</p>
        <div className="grid grid-cols-2 gap-1 text-xs text-emerald-800">
          <p>Días no usados: <strong>{preview.unusedDays}</strong></p>
          <p>Tasa diaria plan actual: <strong>${preview.currentDailyRate.toLocaleString()}</strong></p>
          <p>Crédito total: <strong>${preview.creditAmount.toLocaleString()}</strong></p>
          <p>Nuevo plan ({preview.newTotalDays} días): <strong>${preview.newPlanTotal.toLocaleString()}</strong></p>
        </div>
      </div>

      <div className="bg-emerald-100 border border-emerald-300 rounded p-3">
        <p className="text-sm text-emerald-900">
          Precio final (con crédito aplicado): <strong className="text-lg">${preview.finalPrice.toLocaleString()}</strong>
        </p>
        <p className="text-xs text-emerald-700 mt-1">
          Ahorro: ${(preview.newPlanTotal - preview.finalPrice).toLocaleString()}
        </p>
      </div>
    </div>
  );
}
export default CambiarPlanPreview;