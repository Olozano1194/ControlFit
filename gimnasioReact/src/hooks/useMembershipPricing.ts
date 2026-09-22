import { useMemo, useState, useCallback } from 'react';
import type { Membresia } from '../model/memberShips.model';
import { DISCOUNT_TIERS } from '../constants/pricing';
import { calculateEstimatedPrice, calculateTotalDays } from '../utils/pricing';
import { calculateEstimatedDateFinal } from '../utils/dateUtils';

export interface UseMembershipPricingReturn {
  estimatedPrice: number;
  totalDays: number;
  estimatedDateFinal: string;
  multiplierOptions: number[];
  showMultiplier: boolean;
  selectedMembresia: Membresia | null;
  multiplier: number;
  discountPercent: number;
  setMultiplier: (val: number) => void;
  setDiscountPercent: (val: number) => void;
  setSelectedMembresia: (m: Membresia | null) => void;
  setDateInitial: (date: string) => void;
}

export function useMembershipPricing(
  initialMembresia: Membresia | null = null
): UseMembershipPricingReturn {
  const [selectedMembresia, setSelectedMembresiaState] = useState<Membresia | null>(initialMembresia);
  const [multiplier, setMultiplierState] = useState<number>(1);
  const [discountPercent, setDiscountPercentState] = useState<number>(0);
  const [dateInitial, setDateInitialState] = useState<string>('');

  const setSelectedMembresia = useCallback((m: Membresia | null) => {
    setSelectedMembresiaState(m);
    setMultiplierState(1);
    setDiscountPercentState(0);
  }, []);

  const setMultiplier = useCallback((val: number) => {
    setMultiplierState(val);
    // Auto-apply discount tier when multiplier changes
    const discount = DISCOUNT_TIERS[val as keyof typeof DISCOUNT_TIERS] ?? 0;
    setDiscountPercentState(discount);
  }, []);

  const setDiscountPercent = useCallback((val: number) => {
    // Clamp discount between 0 and 100
    const clamped = Math.max(0, Math.min(100, val));
    setDiscountPercentState(clamped);
  }, []);

  const setDateInitial = useCallback((date: string) => {
    setDateInitialState(date);
  }, []);

  const multiplierOptions = useMemo(() => {
    if (!selectedMembresia || selectedMembresia.max_multiplier < 1) {
      return [];
    }
    return Array.from({ length: selectedMembresia.max_multiplier }, (_, i) => i + 1);
  }, [selectedMembresia]);

  const showMultiplier = useMemo(() => {
    return selectedMembresia !== null && selectedMembresia.max_multiplier > 1;
  }, [selectedMembresia]);

  const estimatedPrice = useMemo(() => {
    if (!selectedMembresia) return 0;
    return calculateEstimatedPrice(selectedMembresia.price, multiplier, discountPercent);
  }, [selectedMembresia, multiplier, discountPercent]);

  const totalDays = useMemo(() => {
    if (!selectedMembresia) return 0;
    return calculateTotalDays(selectedMembresia.duration, multiplier);
  }, [selectedMembresia, multiplier]);

  const estimatedDateFinal = useMemo(() => {
    if (!dateInitial || !selectedMembresia) return '';
    return calculateEstimatedDateFinal(dateInitial, totalDays);
  }, [dateInitial, selectedMembresia, totalDays]);

  return {
    estimatedPrice,
    totalDays,
    estimatedDateFinal,
    multiplierOptions,
    showMultiplier,
    selectedMembresia,
    multiplier,
    discountPercent,
    setMultiplier,
    setDiscountPercent,
    setSelectedMembresia,
    setDateInitial,
  };
}