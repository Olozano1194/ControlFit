interface RefundPreviewProps {
  previewRemainingBalance: string;
  currentSaldoPendiente: string | number;
}

export function RefundPreview({
  previewRemainingBalance,
  currentSaldoPendiente,
}: RefundPreviewProps) {
  const saldo = parseFloat(currentSaldoPendiente as unknown as string) || 0;

  if (!previewRemainingBalance) {
    return (
      <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
        <p className="text-sm text-gray-600">
          Ingrese un monto válido para ver el saldo restante después de la devolución.
        </p>
      </div>
    );
  }

  const remaining = parseFloat(previewRemainingBalance);

  return (
    <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
      <h3 className="text-sm font-medium text-green-800 mb-2">Vista previa de la devolución</h3>
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-green-700 font-medium">Saldo actual</p>
          <p className="text-green-900">${saldo.toLocaleString('es-CO', { minimumFractionDigits: 2 })}</p>
        </div>
        <div>
          <p className="text-green-700 font-medium">Saldo después de la devolución</p>
          <p className="text-green-900 font-bold">${remaining.toLocaleString('es-CO', { minimumFractionDigits: 2 })}</p>
        </div>
      </div>
      {remaining === 0 && (
        <p className="text-xs text-green-700 mt-2">
          La membresía quedará con estado de pago <strong>Pendiente</strong> (sin pagos registrados).
        </p>
      )}
      {remaining > 0 && (
        <p className="text-xs text-green-700 mt-2">
          La membresía quedará con estado de pago <strong>Parcial</strong>.
        </p>
      )}
    </div>
  );
}
export default RefundPreview;