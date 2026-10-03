interface SuspenderPreviewProps {
  previewDateFinal: string;
  currentDateFinal: string;
}

export function SuspenderPreview({ previewDateFinal, currentDateFinal }: SuspenderPreviewProps) {
  if (!previewDateFinal) return null;

  const extensionDays = Math.ceil(
    (new Date(previewDateFinal).getTime() - new Date(currentDateFinal).getTime()) / (1000 * 60 * 60 * 24)
  );

  return (
    <div className="p-4 bg-sky-50 border border-sky-200 rounded-lg">
      <p className="text-sm font-medium text-sky-800">Vista previa</p>
      <p className="text-sm text-sky-700">
        Fecha final actual: <strong>{currentDateFinal}</strong>
      </p>
      <p className="text-sm text-sky-700">
        Nueva fecha final: <strong>{previewDateFinal}</strong>
      </p>
      <p className="text-sm text-sky-700">
        Días de extensión: <strong>{extensionDays}</strong>
      </p>
    </div>
  );
}
export default SuspenderPreview;