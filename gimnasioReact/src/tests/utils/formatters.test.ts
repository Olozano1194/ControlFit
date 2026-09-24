import { describe, it, expect } from 'vitest';
import { formatCurrencyCOP } from '../../utils/formatters';

// Intl.NumberFormat uses non-breaking space (U+00A0) between symbol and number
const NBSP = '\u00A0';

describe('formatters', () => {
  describe('formatCurrencyCOP', () => {
    it('should format zero correctly', () => {
      expect(formatCurrencyCOP(0)).toBe(`$${NBSP}0`);
    });

    it('should format positive integers correctly', () => {
      expect(formatCurrencyCOP(1000)).toBe(`$${NBSP}1.000`);
      expect(formatCurrencyCOP(10000)).toBe(`$${NBSP}10.000`);
      expect(formatCurrencyCOP(100000)).toBe(`$${NBSP}100.000`);
      expect(formatCurrencyCOP(1000000)).toBe(`$${NBSP}1.000.000`);
    });

    it('should format negative numbers correctly', () => {
      expect(formatCurrencyCOP(-1000)).toBe(`-$${NBSP}1.000`);
      expect(formatCurrencyCOP(-10000)).toBe(`-$${NBSP}10.000`);
    });

    it('should handle decimals (rounds to 0 decimals)', () => {
      expect(formatCurrencyCOP(1000.50)).toBe(`$${NBSP}1.001`);
      expect(formatCurrencyCOP(1000.49)).toBe(`$${NBSP}1.000`);
      expect(formatCurrencyCOP(1000.99)).toBe(`$${NBSP}1.001`);
    });

    it('should handle large numbers', () => {
      expect(formatCurrencyCOP(999999999)).toBe(`$${NBSP}999.999.999`);
    });

    it('should use Colombian peso format with dots as thousand separators', () => {
      // es-CO uses dots for thousands, no decimals
      expect(formatCurrencyCOP(1234567)).toBe(`$${NBSP}1.234.567`);
    });
  });
});