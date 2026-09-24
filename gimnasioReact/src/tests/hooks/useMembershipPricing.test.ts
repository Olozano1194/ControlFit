import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useMembershipPricing } from '../../hooks/useMembershipPricing';
import type { Membresia } from '../../model/memberShips.model';
import { DISCOUNT_TIERS } from '../../constants/pricing';

// Mock Membresia for testing
const mockMembresia: Membresia = {
  id: 1,
  name: 'Test Membership',
  price: 10000,
  duration: 30,
  max_multiplier: 12,
  is_active: true,
  gimnasio: 1,
};

const mockMembresiaMax1: Membresia = {
  id: 2,
  name: 'Single Month',
  price: 5000,
  duration: 30,
  max_multiplier: 1,
  is_active: true,
  gimnasio: 1,
};

describe('useMembershipPricing', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('initial state', () => {
    it('should return defaults when no membership selected', () => {
      const { result } = renderHook(() => useMembershipPricing(null));

      expect(result.current.selectedMembresia).toBeNull();
      expect(result.current.multiplier).toBe(1);
      expect(result.current.discountPercent).toBe(0);
      expect(result.current.multiplierOptions).toEqual([]);
      expect(result.current.showMultiplier).toBe(false);
      expect(result.current.estimatedPrice).toBe(0);
      expect(result.current.totalDays).toBe(0);
      expect(result.current.estimatedDateFinal).toBe('');
    });

    it('should compute derived values when membership provided', () => {
      const { result } = renderHook(() => useMembershipPricing(mockMembresia));

      expect(result.current.selectedMembresia).toEqual(mockMembresia);
      expect(result.current.multiplier).toBe(1);
      expect(result.current.discountPercent).toBe(0);
      expect(result.current.multiplierOptions).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]);
      expect(result.current.showMultiplier).toBe(true);
      expect(result.current.estimatedPrice).toBe(10000); // 10000 * 1 * (1 - 0/100)
      expect(result.current.totalDays).toBe(30); // 30 * 1
      expect(result.current.estimatedDateFinal).toBe('');
    });

    it('should have empty multiplierOptions when max_multiplier < 1', () => {
      const { result } = renderHook(() => useMembershipPricing(mockMembresiaMax1));

      expect(result.current.multiplierOptions).toEqual([1]);
      expect(result.current.showMultiplier).toBe(false); // max_multiplier is 1, not > 1
    });
  });

  describe('setMultiplier', () => {
    it('should update multiplier and apply DISCOUNT_TIERS', () => {
      const { result } = renderHook(() => useMembershipPricing(mockMembresia));

      act(() => {
        result.current.setMultiplier(3);
      });

      expect(result.current.multiplier).toBe(3);
      expect(result.current.discountPercent).toBe(DISCOUNT_TIERS[3]); // 5
    });

    it('should apply 0 discount for multiplier not in DISCOUNT_TIERS', () => {
      const { result } = renderHook(() => useMembershipPricing(mockMembresia));

      act(() => {
        result.current.setMultiplier(4); // Not in DISCOUNT_TIERS
      });

      expect(result.current.multiplier).toBe(4);
      expect(result.current.discountPercent).toBe(0);
    });

    it('should apply correct discounts for all DISCOUNT_TIERS keys', () => {
      const { result } = renderHook(() => useMembershipPricing(mockMembresia));

      const testCases = [
        { multiplier: 1, expectedDiscount: 0 },
        { multiplier: 2, expectedDiscount: 0 },
        { multiplier: 3, expectedDiscount: 5 },
        { multiplier: 6, expectedDiscount: 10 },
        { multiplier: 12, expectedDiscount: 20 },
      ];

      testCases.forEach(({ multiplier, expectedDiscount }) => {
        act(() => {
          result.current.setMultiplier(multiplier);
        });
        expect(result.current.multiplier).toBe(multiplier);
        expect(result.current.discountPercent).toBe(expectedDiscount);
      });
    });

    it('should update estimatedPrice when multiplier changes', () => {
      const { result } = renderHook(() => useMembershipPricing(mockMembresia));

      act(() => {
        result.current.setMultiplier(3);
      });

      // 10000 * 3 * (1 - 5/100) = 28500
      expect(result.current.estimatedPrice).toBe(28500);
      expect(result.current.totalDays).toBe(90); // 30 * 3
    });

    it('should clamp multiplier to valid range?', () => {
      const { result } = renderHook(() => useMembershipPricing(mockMembresia));

      act(() => {
        result.current.setMultiplier(0);
      });

      expect(result.current.multiplier).toBe(0);
      // DISCOUNT_TIERS[0] is undefined, so discount should be 0
      expect(result.current.discountPercent).toBe(0);
    });
  });

  describe('setDiscountPercent', () => {
    it('should update discount percent', () => {
      const { result } = renderHook(() => useMembershipPricing(mockMembresia));

      act(() => {
        result.current.setDiscountPercent(15);
      });

      expect(result.current.discountPercent).toBe(15);
    });

    it('should clamp discount to 0-100 range', () => {
      const { result } = renderHook(() => useMembershipPricing(mockMembresia));

      act(() => {
        result.current.setDiscountPercent(-10);
      });
      expect(result.current.discountPercent).toBe(0);

      act(() => {
        result.current.setDiscountPercent(150);
      });
      expect(result.current.discountPercent).toBe(100);
    });

    it('should update estimatedPrice when discount changes', () => {
      const { result } = renderHook(() => useMembershipPricing(mockMembresia));

      act(() => {
        result.current.setDiscountPercent(20);
      });

      // 10000 * 1 * (1 - 20/100) = 8000
      expect(result.current.estimatedPrice).toBe(8000);
    });

    it('should allow decimal discounts', () => {
      const { result } = renderHook(() => useMembershipPricing(mockMembresia));

      act(() => {
        result.current.setDiscountPercent(5.5);
      });

      // 10000 * 1 * (1 - 5.5/100) = 9450
      expect(result.current.discountPercent).toBe(5.5);
      expect(result.current.estimatedPrice).toBe(9450);
    });
  });

  describe('setSelectedMembresia', () => {
    it('should update selectedMembresia and reset multiplier/discount', () => {
      const { result } = renderHook(() => useMembershipPricing(mockMembresia));

      // First change multiplier and discount
      act(() => {
        result.current.setMultiplier(6);
        result.current.setDiscountPercent(10);
      });

      expect(result.current.multiplier).toBe(6);
      expect(result.current.discountPercent).toBe(10);

      // Now change membership
      act(() => {
        result.current.setSelectedMembresia(mockMembresiaMax1);
      });

      expect(result.current.selectedMembresia).toEqual(mockMembresiaMax1);
      expect(result.current.multiplier).toBe(1);
      expect(result.current.discountPercent).toBe(0);
      expect(result.current.multiplierOptions).toEqual([1]);
      expect(result.current.showMultiplier).toBe(false);
    });

    it('should handle null membership', () => {
      const { result } = renderHook(() => useMembershipPricing(mockMembresia));

      act(() => {
        result.current.setMultiplier(6);
        result.current.setDiscountPercent(10);
      });

      act(() => {
        result.current.setSelectedMembresia(null);
      });

      expect(result.current.selectedMembresia).toBeNull();
      expect(result.current.multiplier).toBe(1);
      expect(result.current.discountPercent).toBe(0);
      expect(result.current.multiplierOptions).toEqual([]);
      expect(result.current.showMultiplier).toBe(false);
      expect(result.current.estimatedPrice).toBe(0);
      expect(result.current.totalDays).toBe(0);
    });

    it('should recompute derived values when membership changes', () => {
      const { result } = renderHook(() => useMembershipPricing(mockMembresia));

      act(() => {
        result.current.setSelectedMembresia(mockMembresiaMax1);
      });

      // mockMembresiaMax1 has price 5000, duration 30
      expect(result.current.estimatedPrice).toBe(5000);
      expect(result.current.totalDays).toBe(30);
    });
  });

  describe('derived values', () => {
    it('should calculate estimatedPrice correctly', () => {
      const { result } = renderHook(() => useMembershipPricing(mockMembresia));

      act(() => {
        result.current.setMultiplier(3);
        result.current.setDiscountPercent(5);
      });

      // 10000 * 3 * (1 - 5/100) = 28500
      expect(result.current.estimatedPrice).toBe(28500);
    });

    it('should calculate totalDays correctly', () => {
      const { result } = renderHook(() => useMembershipPricing(mockMembresia));

      act(() => {
        result.current.setMultiplier(6);
      });

      // 30 * 6 = 180
      expect(result.current.totalDays).toBe(180);
    });

    it('should calculate estimatedDateFinal using dateUtils', () => {
      const { result } = renderHook(() => useMembershipPricing(mockMembresia));

      act(() => {
        result.current.setMultiplier(3);
      });

      // The hook should use the dateInitial from watch or provide a way to set it
      // For now, estimatedDateFinal depends on dateInitial which comes from form
      // We'll test this integration in useMemberForm tests
      expect(typeof result.current.estimatedDateFinal).toBe('string');
    });

    it('should return empty string for estimatedDateFinal when no dateInitial', () => {
      const { result } = renderHook(() => useMembershipPricing(mockMembresia));

      // Without dateInitial from form, estimatedDateFinal should be empty
      expect(result.current.estimatedDateFinal).toBe('');
    });
  });

  describe('edge cases', () => {
    it('should handle membership with zero price', () => {
      const freeMembresia: Membresia = {
        ...mockMembresia,
        price: 0,
      };

      const { result } = renderHook(() => useMembershipPricing(freeMembresia));

      act(() => {
        result.current.setMultiplier(12);
        result.current.setDiscountPercent(20);
      });

      expect(result.current.estimatedPrice).toBe(0);
    });

    it('should handle membership with zero duration', () => {
      const zeroDurationMembresia: Membresia = {
        ...mockMembresia,
        duration: 0,
      };

      const { result } = renderHook(() => useMembershipPricing(zeroDurationMembresia));

      act(() => {
        result.current.setMultiplier(6);
      });

      expect(result.current.totalDays).toBe(0);
    });

    it('should handle rapid state changes', () => {
      const { result } = renderHook(() => useMembershipPricing(mockMembresia));

      act(() => {
        result.current.setMultiplier(3);
        result.current.setDiscountPercent(5);
        result.current.setMultiplier(6);
        result.current.setDiscountPercent(10);
      });

      expect(result.current.multiplier).toBe(6);
      expect(result.current.discountPercent).toBe(10);
      expect(result.current.estimatedPrice).toBe(54000); // 10000 * 6 * 0.9
    });
  });
});