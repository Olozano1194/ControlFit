import type { PaymentSummaryProps } from '../../types/MemberFormTypes';
import { formatCurrencyCOP } from '../../utils/formatters';
import { formatDateForDisplay } from '../../utils/dateUtils';

export function PaymentSummary({
  selectedMembresia,
  multiplier,
  discountPercent,
  estimatedPrice,
  totalDays,
  estimatedDateFinal,
  disabled = false,
}: PaymentSummaryProps) {
  if (!selectedMembresia || Number(selectedMembresia.price) <= 0) {
    return null;
  }

  const unitPrice = Number(selectedMembresia.price);
  const discountAmount = unitPrice * multiplier * (discountPercent / 100);

  return (
    <div className={`bg-gray-50 p-4 rounded-lg border border-gray-200 ${disabled ? 'opacity-50' : ''}`}>
      <p className="text-sm text-gray-500 uppercase tracking-wider font-semibold mb-2">Resumen del pago</p>
      <div className="space-y-1 text-sm">
        <div className="flex justify-between">
          <span>Membresía:</span>
          <span className="font-medium">{selectedMembresia.name}</span>
        </div>
        <div className="flex justify-between">
          <span>Valor unitario:</span>
          <span>{formatCurrencyCOP(unitPrice)}</span>
        </div>
        <div className="flex justify-between">
          <span>Fecha inicio:</span>
          <span>{formatDateForDisplay(estimatedDateFinal) || '-'}</span>
        </div>
        <div className="flex justify-between">
          <span>Fecha fin:</span>
          <span>{estimatedDateFinal || '-'}</span>
        </div>
        <div className="flex justify-between">
          <span>Días totales:</span>
          <span>{totalDays} días</span>
        </div>
        <div className="flex justify-between">
          <span>Multiplicador:</span>
          <span>{multiplier}x</span>
        </div>
        {discountPercent > 0 && (
          <div className="flex justify-between text-green-600">
            <span>Descuento ({discountPercent}%):</span>
            <span>-{formatCurrencyCOP(discountAmount)}</span>
          </div>
        )}
        <div className="flex justify-between font-bold text-base pt-2 border-t border-gray-200 mt-2">
          <span>Total a pagar:</span>
          <span>{formatCurrencyCOP(estimatedPrice)}</span>
        </div>
      </div>
    </div>
  );
}