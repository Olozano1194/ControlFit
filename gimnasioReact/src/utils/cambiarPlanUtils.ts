import type { AsignarMemberShips } from '@/model/asignarMemberShips.model';
import type { Membresia } from '@/model/memberShips.model';

export interface CambiarPlanPreviewData {
  creditAmount: number;
  unusedDays: number;
  currentDailyRate: number;
  newPlanBasePrice: number;
  newPlanTotal: number;
  finalPrice: number;
  newDateFinal: string;
  newTotalDays: number;
}

/**
 * Calculate preview data for cambiar-plan operation.
 * 
 * @param asignacion - Current assignment being changed
 * @param selectedMembresia - New membership selected
 * @param currentMembresia - Current membership from the list
 * @param multiplier - New multiplier (1 to max_multiplier)
 * @param discountPercent - New discount percentage (0-100)
 * @returns Preview data or null if insufficient data
 */
export function calculateCambiarPlanPreview(
  asignacion: AsignarMemberShips | null,
  selectedMembresia: Membresia | null,
  currentMembresia: Membresia | null,
  multiplier: number,
  discountPercent: number
): CambiarPlanPreviewData | null {
  if (!asignacion || !selectedMembresia || !currentMembresia) {
    return null;
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  // Current plan calculations
  const currentMultiplier = parseFloat(asignacion.multiplier as unknown as string) || 1;
  const currentTotalDays = currentMembresia.duration * currentMultiplier;
  const currentPrice = parseFloat(asignacion.price as unknown as string) || 0;
  const currentDailyRate = currentTotalDays > 0 ? currentPrice / currentTotalDays : 0;

  // Unused days
  const dateFinal = new Date(asignacion.dateFinal);
  const unusedDays = Math.max(0, Math.ceil((dateFinal.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)));
  const creditAmount = unusedDays * currentDailyRate;

  // New plan calculations
  const newMultiplier = multiplier || 1;
  const newDiscount = discountPercent || 0;
  const newPlanBasePrice = selectedMembresia.price * newMultiplier;
  const newPlanTotal = newPlanBasePrice * (1 - newDiscount / 100);
  const finalPrice = Math.max(0, newPlanTotal - creditAmount);

  // New dates
  const newTotalDays = selectedMembresia.duration * newMultiplier;
  const newDateFinal = new Date(today);
  newDateFinal.setDate(newDateFinal.getDate() + newTotalDays);

  return {
    creditAmount: Math.round(creditAmount * 100) / 100,
    unusedDays,
    currentDailyRate: Math.round(currentDailyRate * 100) / 100,
    newPlanBasePrice: Math.round(newPlanBasePrice * 100) / 100,
    newPlanTotal: Math.round(newPlanTotal * 100) / 100,
    finalPrice: Math.round(finalPrice * 100) / 100,
    newDateFinal: newDateFinal.toISOString().split('T')[0],
    newTotalDays,
  };
}