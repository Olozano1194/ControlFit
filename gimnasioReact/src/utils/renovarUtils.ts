import type { AsignarMemberShips } from '@/model/asignarMemberShips.model';
import type { Membresia } from '@/model/memberShips.model';

export interface RenovarPreviewData {
  dateInitial: string;
  dateFinal: string;
  price: number;
  totalDays: number;
  isValid: boolean;
}

export function calculateRenovarPreview(
  asignacion: AsignarMemberShips | null,
  selectedMembresia: Membresia | null,
  currentMembresia: Membresia | null,
  multiplier: number,
  discountPercent: number
): RenovarPreviewData {
  const today = new Date();
  const membership = selectedMembresia || currentMembresia;

  if (!membership || !asignacion) {
    return {
      dateInitial: '',
      dateFinal: '',
      price: 0,
      totalDays: 0,
      isValid: false,
    };
  }

  // dateInitial = today
  const dateInitial = today;
  const totalDays = membership.duration * multiplier;
  const dateFinal = new Date(today);
  dateFinal.setDate(dateFinal.getDate() + totalDays);

  // price = membership.price * multiplier * (1 - discount/100)
  const price = membership.price * multiplier * (1 - discountPercent / 100);

  return {
    dateInitial: dateInitial.toISOString().split('T')[0],
    dateFinal: dateFinal.toISOString().split('T')[0],
    price: Math.round(price * 100) / 100,
    totalDays,
    isValid: true,
  };
}