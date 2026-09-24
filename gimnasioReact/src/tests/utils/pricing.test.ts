import { describe, it, expect } from 'vitest';
import { calculateEstimatedPrice, calculateTotalDays } from '../../utils/pricing';

describe('pricing utils', () => {
  describe('calculateEstimatedPrice', () => {
    it('should calculate price correctly for happy path', () => {
      // base * multiplier * (1 - discount/100)
      expect(calculateEstimatedPrice(10000, 1, 0)).toBe(10000);
      expect(calculateEstimatedPrice(10000, 3, 0)).toBe(30000);
      expect(calculateEstimatedPrice(10000, 3, 5)).toBe(28500); // 30000 * 0.95
      expect(calculateEstimatedPrice(10000, 6, 10)).toBe(54000); // 60000 * 0.90
      expect(calculateEstimatedPrice(10000, 12, 20)).toBe(96000); // 120000 * 0.80
    });

    it('should handle zero price', () => {
      expect(calculateEstimatedPrice(0, 1, 0)).toBe(0);
      expect(calculateEstimatedPrice(0, 12, 20)).toBe(0);
    });

    it('should handle zero multiplier', () => {
      expect(calculateEstimatedPrice(10000, 0, 0)).toBe(0);
      expect(calculateEstimatedPrice(10000, 0, 20)).toBe(0);
    });

    it('should handle zero discount', () => {
      expect(calculateEstimatedPrice(10000, 1, 0)).toBe(10000);
      expect(calculateEstimatedPrice(10000, 12, 0)).toBe(120000);
    });

    it('should handle decimal prices', () => {
      expect(calculateEstimatedPrice(10000.50, 1, 0)).toBe(10000.50);
      expect(calculateEstimatedPrice(10000.50, 2, 0)).toBe(20001);
    });

    it('should handle decimal discounts', () => {
      // 10000 * 1 * (1 - 5.5/100) = 10000 * 0.945 = 9450
      expect(calculateEstimatedPrice(10000, 1, 5.5)).toBe(9450);
    });

    it('should handle large numbers', () => {
      expect(calculateEstimatedPrice(1000000, 12, 20)).toBe(9600000);
    });

    it('should handle negative discount (should increase price)', () => {
      // Negative discount = price increase
      expect(calculateEstimatedPrice(10000, 1, -10)).toBe(11000);
    });

    it('should handle negative multiplier (edge case)', () => {
      // Negative multiplier
      expect(calculateEstimatedPrice(10000, -1, 0)).toBe(-10000);
    });

    it('should handle negative price (edge case)', () => {
      expect(calculateEstimatedPrice(-10000, 1, 0)).toBe(-10000);
    });
  });

  describe('calculateTotalDays', () => {
    it('should calculate total days correctly for happy path', () => {
      // duration * multiplier
      expect(calculateTotalDays(30, 1)).toBe(30);
      expect(calculateTotalDays(30, 3)).toBe(90);
      expect(calculateTotalDays(30, 6)).toBe(180);
      expect(calculateTotalDays(30, 12)).toBe(360);
    });

    it('should handle zero duration', () => {
      expect(calculateTotalDays(0, 1)).toBe(0);
      expect(calculateTotalDays(0, 12)).toBe(0);
    });

    it('should handle zero multiplier', () => {
      expect(calculateTotalDays(30, 0)).toBe(0);
    });

    it('should handle decimal duration', () => {
      expect(calculateTotalDays(30.5, 2)).toBe(61);
    });

    it('should handle large numbers', () => {
      expect(calculateTotalDays(365, 12)).toBe(4380);
    });

    it('should handle negative values (edge case)', () => {
      expect(calculateTotalDays(-30, 1)).toBe(-30);
      expect(calculateTotalDays(30, -1)).toBe(-30);
    });
  });
});