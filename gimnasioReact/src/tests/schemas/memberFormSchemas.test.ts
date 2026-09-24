import { describe, it, expect } from 'vitest';
import { existingMemberSchema, newMemberSchema, memberFormSchema } from '../../schemas/memberFormSchemas';

describe('memberFormSchemas', () => {
  describe('existingMemberSchema', () => {
    it('should validate required fields for existing member mode', () => {
      const validData = {
        miembro: '1',
        membresia: '1',
        dateInitial: '2026-01-15',
      };
      const result = existingMemberSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    it('should require miembro field', () => {
      const data = {
        membresia: '1',
        dateInitial: '2026-01-15',
      };
      const result = existingMemberSchema.safeParse(data);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues.some(i => i.path.includes('miembro'))).toBe(true);
      }
    });

    it('should require membresia field', () => {
      const data = {
        miembro: '1',
        dateInitial: '2026-01-15',
      };
      const result = existingMemberSchema.safeParse(data);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues.some(i => i.path.includes('membresia'))).toBe(true);
      }
    });

    it('should require dateInitial field', () => {
      const data = {
        miembro: '1',
        membresia: '1',
      };
      const result = existingMemberSchema.safeParse(data);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues.some(i => i.path.includes('dateInitial'))).toBe(true);
      }
    });

    it('should NOT require nuevoName, nuevoLastname, nuevoPhone for existing member', () => {
      const data = {
        miembro: '1',
        membresia: '1',
        dateInitial: '2026-01-15',
      };
      const result = existingMemberSchema.safeParse(data);
      expect(result.success).toBe(true);
    });
  });

  describe('newMemberSchema', () => {
    it('should validate required fields for new member mode', () => {
      const validData = {
        nuevoName: 'Juan',
        nuevoLastname: 'Perez',
        nuevoPhone: '3001234567',
        nuevoAddress: 'Calle 123',
        membresia: '1',
        dateInitial: '2026-01-15',
      };
      const result = newMemberSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    it('should require nuevoName with min 4 chars, max 20, only letters', () => {
      // Too short
      let result = newMemberSchema.safeParse({
        nuevoName: 'Jo',
        nuevoLastname: 'Perez',
        nuevoPhone: '3001234567',
        membresia: '1',
        dateInitial: '2026-01-15',
      });
      expect(result.success).toBe(false);

      // Too long
      result = newMemberSchema.safeParse({
        nuevoName: 'JuanCarlosMiguelAngel',
        nuevoLastname: 'Perez',
        nuevoPhone: '3001234567',
        membresia: '1',
        dateInitial: '2026-01-15',
      });
      expect(result.success).toBe(false);

      // Invalid chars (numbers)
      result = newMemberSchema.safeParse({
        nuevoName: 'Juan123',
        nuevoLastname: 'Perez',
        nuevoPhone: '3001234567',
        membresia: '1',
        dateInitial: '2026-01-15',
      });
      expect(result.success).toBe(false);

      // Valid name
      result = newMemberSchema.safeParse({
        nuevoName: 'Juan',
        nuevoLastname: 'Perez',
        nuevoPhone: '3001234567',
        membresia: '1',
        dateInitial: '2026-01-15',
      });
      expect(result.success).toBe(true);
    });

    it('should require nuevoLastname with min 5 chars, max 20, only letters', () => {
      // Too short
      let result = newMemberSchema.safeParse({
        nuevoName: 'Juan',
        nuevoLastname: 'Per',
        nuevoPhone: '3001234567',
        membresia: '1',
        dateInitial: '2026-01-15',
      });
      expect(result.success).toBe(false);

      // Too long
      result = newMemberSchema.safeParse({
        nuevoName: 'Juan',
        nuevoLastname: 'PerezGonzalezRodriguez',
        nuevoPhone: '3001234567',
        membresia: '1',
        dateInitial: '2026-01-15',
      });
      expect(result.success).toBe(false);

      // Invalid chars
      result = newMemberSchema.safeParse({
        nuevoName: 'Juan',
        nuevoLastname: 'Perez123',
        nuevoPhone: '3001234567',
        membresia: '1',
        dateInitial: '2026-01-15',
      });
      expect(result.success).toBe(false);

      // Valid lastname
      result = newMemberSchema.safeParse({
        nuevoName: 'Juan',
        nuevoLastname: 'Perez',
        nuevoPhone: '3001234567',
        membresia: '1',
        dateInitial: '2026-01-15',
      });
      expect(result.success).toBe(true);
    });

    it('should require nuevoPhone with exactly 10 digits', () => {
      // Too short
      let result = newMemberSchema.safeParse({
        nuevoName: 'Juan',
        nuevoLastname: 'Perez',
        nuevoPhone: '300123456',
        membresia: '1',
        dateInitial: '2026-01-15',
      });
      expect(result.success).toBe(false);

      // Too long
      result = newMemberSchema.safeParse({
        nuevoName: 'Juan',
        nuevoLastname: 'Perez',
        nuevoPhone: '30012345678',
        membresia: '1',
        dateInitial: '2026-01-15',
      });
      expect(result.success).toBe(false);

      // Non-digits
      result = newMemberSchema.safeParse({
        nuevoName: 'Juan',
        nuevoLastname: 'Perez',
        nuevoPhone: '300123456a',
        membresia: '1',
        dateInitial: '2026-01-15',
      });
      expect(result.success).toBe(false);

      // Valid phone
      result = newMemberSchema.safeParse({
        nuevoName: 'Juan',
        nuevoLastname: 'Perez',
        nuevoPhone: '3001234567',
        membresia: '1',
        dateInitial: '2026-01-15',
      });
      expect(result.success).toBe(true);
    });

    it('should allow optional nuevoAddress with max 50 chars', () => {
      // Valid without address
      let result = newMemberSchema.safeParse({
        nuevoName: 'Juan',
        nuevoLastname: 'Perez',
        nuevoPhone: '3001234567',
        membresia: '1',
        dateInitial: '2026-01-15',
      });
      expect(result.success).toBe(true);

      // Valid with address
      result = newMemberSchema.safeParse({
        nuevoName: 'Juan',
        nuevoLastname: 'Perez',
        nuevoPhone: '3001234567',
        nuevoAddress: 'Calle 123 #45-67',
        membresia: '1',
        dateInitial: '2026-01-15',
      });
      expect(result.success).toBe(true);

      // Too long address
      result = newMemberSchema.safeParse({
        nuevoName: 'Juan',
        nuevoLastname: 'Perez',
        nuevoPhone: '3001234567',
        nuevoAddress: 'A'.repeat(51),
        membresia: '1',
        dateInitial: '2026-01-15',
      });
      expect(result.success).toBe(false);
    });

    it('should require membresia and dateInitial', () => {
      // Missing membresia
      let result = newMemberSchema.safeParse({
        nuevoName: 'Juan',
        nuevoLastname: 'Perez',
        nuevoPhone: '3001234567',
        dateInitial: '2026-01-15',
      });
      expect(result.success).toBe(false);

      // Missing dateInitial
      result = newMemberSchema.safeParse({
        nuevoName: 'Juan',
        nuevoLastname: 'Perez',
        nuevoPhone: '3001234567',
        membresia: '1',
      });
      expect(result.success).toBe(false);
    });

    it('should NOT require miembro for new member', () => {
      const data = {
        nuevoName: 'Juan',
        nuevoLastname: 'Perez',
        nuevoPhone: '3001234567',
        membresia: '1',
        dateInitial: '2026-01-15',
      };
      const result = newMemberSchema.safeParse(data);
      expect(result.success).toBe(true);
    });
  });

  describe('memberFormSchema factory', () => {
    it('should return existingMemberSchema for modo "existente"', () => {
      const schema = memberFormSchema('existente');
      const result = schema.safeParse({
        miembro: '1',
        membresia: '1',
        dateInitial: '2026-01-15',
      });
      expect(result.success).toBe(true);
    });

    it('should return newMemberSchema for modo "nuevo"', () => {
      const schema = memberFormSchema('nuevo');
      const result = schema.safeParse({
        nuevoName: 'Juan',
        nuevoLastname: 'Perez',
        nuevoPhone: '3001234567',
        membresia: '1',
        dateInitial: '2026-01-15',
      });
      expect(result.success).toBe(true);
    });
  });
});