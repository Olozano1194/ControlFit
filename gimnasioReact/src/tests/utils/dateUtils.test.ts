import { describe, it, expect } from 'vitest';
import {
  calculateEstimatedDateFinal,
  formatDateForInput,
  formatDateForDisplay,
} from '../../utils/dateUtils';

describe('dateUtils', () => {
  describe('calculateEstimatedDateFinal', () => {
    it('should calculate final date correctly for happy path', () => {
      // 2026-01-15 + 30 days = 2026-02-14
      expect(calculateEstimatedDateFinal('2026-01-15', 30)).toBe('14/02/2026');
      
      // 2026-01-15 + 90 days = 2026-04-15
      expect(calculateEstimatedDateFinal('2026-01-15', 90)).toBe('15/04/2026');
      
      // 2026-01-15 + 360 days = 2026-12-31 (leap year 2026 is not leap)
      expect(calculateEstimatedDateFinal('2026-01-15', 360)).toBe('10/01/2027');
    });

    it('should handle leap year correctly', () => {
      // 2024 is a leap year - Feb 29 exists
      // 2024-01-15 + 45 days = 2024-02-29
      expect(calculateEstimatedDateFinal('2024-01-15', 45)).toBe('29/02/2024');
      
      // 2024-02-28 + 1 day = 2024-02-29
      expect(calculateEstimatedDateFinal('2024-02-28', 1)).toBe('29/02/2024');
      
      // 2024-02-29 + 1 day = 2024-03-01
      expect(calculateEstimatedDateFinal('2024-02-29', 1)).toBe('01/03/2024');
    });

    it('should handle month boundaries correctly', () => {
      // End of January (31 days) + 1 day = Feb 1
      expect(calculateEstimatedDateFinal('2026-01-31', 1)).toBe('01/02/2026');
      
      // End of February (28 days in 2026) + 1 day = Mar 1
      expect(calculateEstimatedDateFinal('2026-02-28', 1)).toBe('01/03/2026');
      
      // End of April (30 days) + 1 day = May 1
      expect(calculateEstimatedDateFinal('2026-04-30', 1)).toBe('01/05/2026');
      
      // End of December + 1 day = Jan 1 next year
      expect(calculateEstimatedDateFinal('2026-12-31', 1)).toBe('01/01/2027');
    });

    it('should return empty string for invalid dateInitial', () => {
      expect(calculateEstimatedDateFinal('', 30)).toBe('');
      expect(calculateEstimatedDateFinal('invalid', 30)).toBe('');
      expect(calculateEstimatedDateFinal('not-a-date', 30)).toBe('');
    });

    it('should return empty string for invalid totalDays', () => {
      expect(calculateEstimatedDateFinal('2026-01-15', NaN)).toBe('');
      expect(calculateEstimatedDateFinal('2026-01-15', -1)).toBe('');
    });

    it('should handle zero days', () => {
      expect(calculateEstimatedDateFinal('2026-01-15', 0)).toBe('15/01/2026');
    });
  });

  describe('formatDateForInput', () => {
    it('should convert API format (DD-MM-YYYY) to input format (YYYY-MM-DD)', () => {
      expect(formatDateForInput('15-01-2026')).toBe('2026-01-15');
      expect(formatDateForInput('01-01-2026')).toBe('2026-01-01');
      expect(formatDateForInput('31-12-2026')).toBe('2026-12-31');
    });

    it('should handle single digit day/month with padding', () => {
      expect(formatDateForInput('1-1-2026')).toBe('2026-01-01');
      expect(formatDateForInput('5-3-2026')).toBe('2026-03-05');
    });

    it('should return empty string for invalid input', () => {
      expect(formatDateForInput('')).toBe('');
      expect(formatDateForInput('invalid')).toBe('');
      expect(formatDateForInput('2026-01-15')).toBe(''); // Wrong format
    });
  });

  describe('formatDateForDisplay', () => {
    it('should convert input format (YYYY-MM-DD) to display format (DD/MM/YYYY)', () => {
      expect(formatDateForDisplay('2026-01-15')).toBe('15/01/2026');
      expect(formatDateForDisplay('2026-01-01')).toBe('01/01/2026');
      expect(formatDateForDisplay('2026-12-31')).toBe('31/12/2026');
    });

    it('should return empty string for invalid input', () => {
      expect(formatDateForDisplay('')).toBe('');
      expect(formatDateForDisplay('invalid')).toBe('');
      expect(formatDateForDisplay('15-01-2026')).toBe(''); // Wrong format
    });
  });

  describe('roundtrip API ↔ UI', () => {
    it('should maintain date integrity through roundtrip (API → input → display)', () => {
      const apiDate = '15-01-2026';
      const inputDate = formatDateForInput(apiDate);
      const displayDate = formatDateForDisplay(inputDate);
      // display format uses slashes, API uses dashes
      expect(displayDate).toBe('15/01/2026');
    });

    it('should maintain date integrity through reverse roundtrip (input → display → API)', () => {
      const inputDate = '2026-01-15';
      const displayDate = formatDateForDisplay(inputDate);
      const apiDate = formatDateForInput(displayDate);
      expect(apiDate).toBe(inputDate);
    });

    it('should work with various dates', () => {
      const testDates = [
        { api: '01-01-2026', display: '01/01/2026' },
        { api: '28-02-2026', display: '28/02/2026' },
        { api: '29-02-2024', display: '29/02/2024' }, // leap year
        { api: '31-12-2026', display: '31/12/2026' },
        { api: '15-06-2026', display: '15/06/2026' },
      ];
      
      for (const { api, display } of testDates) {
        const inputDate = formatDateForInput(api);
        const displayDate = formatDateForDisplay(inputDate);
        expect(displayDate).toBe(display);
      }
    });
  });
});