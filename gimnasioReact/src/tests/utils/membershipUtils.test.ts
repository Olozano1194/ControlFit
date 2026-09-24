import { describe, it, expect } from 'vitest';
import { generateMultiplierOptions, filterActiveMemberships } from '../../utils/membershipUtils';
import type { SelectedMembresia } from '../../types/MemberFormTypes';

describe('membershipUtils', () => {
  describe('generateMultiplierOptions', () => {
    it('should generate options from 1 to maxMultiplier', () => {
      expect(generateMultiplierOptions(1)).toEqual([1]);
      expect(generateMultiplierOptions(3)).toEqual([1, 2, 3]);
      expect(generateMultiplierOptions(12)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]);
    });

    it('should handle edge cases', () => {
      expect(generateMultiplierOptions(0)).toEqual([]);
      expect(generateMultiplierOptions(-1)).toEqual([]);
    });
  });

  describe('filterActiveMemberships', () => {
    const mockMemberships: SelectedMembresia[] = [
      { id: 1, name: 'Plan A', price: 10000, duration: 30, max_multiplier: 12, is_active: true, gimnasio: 1 },
      { id: 2, name: 'Plan B', price: 20000, duration: 30, max_multiplier: 6, is_active: false, gimnasio: 1 },
      { id: 3, name: 'Plan C', price: 30000, duration: 30, max_multiplier: 3, is_active: true, gimnasio: 1 },
      { id: 4, name: 'Plan D', price: 40000, duration: 30, max_multiplier: 1, is_active: undefined, gimnasio: 1 },
    ];

    it('should return only active memberships (is_active === true)', () => {
      const result = filterActiveMemberships(mockMemberships);
      expect(result).toHaveLength(2);
      expect(result.map(m => m.id)).toEqual([1, 3]);
    });

    it('should exclude inactive memberships (is_active === false)', () => {
      const result = filterActiveMemberships(mockMemberships);
      expect(result.find(m => m.id === 2)).toBeUndefined();
    });

    it('should exclude memberships with undefined is_active', () => {
      const result = filterActiveMemberships(mockMemberships);
      expect(result.find(m => m.id === 4)).toBeUndefined();
    });

    it('should return empty array for empty input', () => {
      expect(filterActiveMemberships([])).toEqual([]);
    });

    it('should return empty array when all are inactive', () => {
      const allInactive = mockMemberships.map(m => ({ ...m, is_active: false }));
      expect(filterActiveMemberships(allInactive)).toEqual([]);
    });

    it('should return all when all are active', () => {
      const allActive = mockMemberships.map(m => ({ ...m, is_active: true }));
      expect(filterActiveMemberships(allActive)).toHaveLength(4);
    });
  });
});